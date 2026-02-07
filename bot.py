
import sys
import os
import time
from dotenv import load_dotenv
from src.signal_lib import SignalClient
from src.anytype_lib import AnytypeClient

# Load environment variables
load_dotenv()

# Configuration
SIGNAL_ACCOUNT = os.getenv("SIGNAL_ACCOUNT")
ANYTYPE_API_KEY = os.getenv("ANYTYPE_API_KEY")
ANYTYPE_API_URL = os.getenv("ANYTYPE_API_URL", "http://localhost:31001/v1")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def main():
    print("=== Signal-Anytype Bridge Bot ===")
    
    if not SIGNAL_ACCOUNT:
        print("Error: SIGNAL_ACCOUNT not found in .env file.")
        return

    # 1. Initialize Signal
    print(f"Using Signal account: {SIGNAL_ACCOUNT}")
    
    signal_client = SignalClient(SIGNAL_ACCOUNT)
    anytype_client = AnytypeClient(token=ANYTYPE_API_KEY)
    
    # Start Polling Thread for Anytype -> Signal
    import threading
    
    def anytype_poller():
        print("Starting Anytype poller...")
        last_check = time.time()
        seen_ids = set()
        
        while True:
            try:
                # 1. Get Spaces
                spaces = anytype_client.get_spaces()
                if spaces:
                    # simplistic: just check first space
                    sid = spaces[0].get('id')
                    
                    # 2. Get Recent Objects
                    objs = anytype_client.get_recent_objects(sid, limit=5)
                    
                    for obj in objs:
                        oid = obj.get('id')
                        # Check if new or modified recently (rudimentary check)
                        # Ideally compare modified_at timestamp vs last_check
                        # For now, just track IDs seen in this session to avoid spamming old stuff,
                        # effectively announcing "Bot Connected" state. 
                        # A real sync needs persistent state.
                        
                        if oid not in seen_ids:
                            seen_ids.add(oid)
                            # Only notify if it looks "fresh" or we assume all unseen are new?
                            # Let's simple-notify for now.
                            title = obj.get('details', {}).get('title') or "Untitled Object"
                            msg = f"🆕 Anytype Update: {title}\nID: {oid}"
                            signal_client.send_message(SIGNAL_ACCOUNT, msg)
                            
                time.sleep(60) # Poll every minute
            except Exception as e:
                print(f"Poller error: {e}")
                time.sleep(60)

    # Only start poller if Anytype is configured/reachable (optional, but good practice)
    # We'll start it anyway.
    poll_thread = threading.Thread(target=anytype_poller, daemon=True)
    poll_thread.start()

    print("Listening for Signal messages...")
    
    for envelope in signal_client.listen_json_rpc():
        source = envelope.get("sourceName") or envelope.get("source")
        message = envelope.get("dataMessage", {}).get("message")
        
        if message:
            print(f"Received from {source}: {message}")
            
            # Process Logic
            # 1. Simple Echo/Log
            # 2. Add to Anytype
            
            # Identify intent (basic keyword search for now)
            obj_type = "Note"
            title = f"Signal from {source}"
            
            if message.lower().startswith("task:"):
                obj_type = "Task"
                message = message[5:].strip()
                title = "New Task"
            
            elif message.lower().startswith("search:") or message.lower().startswith("find:"):
                query = message.split(":", 1)[1].strip()
                print(f"Searching for: {query}")
                results = anytype_client.search_objects(query)
                
                if results:
                    response = f"🔍 Found {len(results)} results for '{query}':\n"
                    for obj in results:
                        oid = obj.get('id')
                        title = obj.get('details', {}).get('title') or "Untitled"
                        response += f"- {title} ({oid})\n"
                else:
                    response = f"❌ No results found for '{query}'"
                
                signal_client.send_message(source, response)
                continue # Skip creation logic
            
            # Send to Anytype
            try:
                result = anytype_client.create_object(obj_type, message, title=title)
                print(f"Anytype result: {result}")
                
                # Confirm receipt
                signal_client.send_message(source, f"Saved to Anytype as {obj_type}!")
            except Exception as e:
                print(f"Error saving to Anytype: {e}")
                signal_client.send_message(source, f"Error saving to Anytype: {e}")

if __name__ == "__main__":
    main()
