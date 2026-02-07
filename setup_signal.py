
import os
import sys
import qrcode
from src.signal_lib import SignalClient, SIGNAL_CLI_PATH
import subprocess

def main():
    print("=== Signal Account Linker ===")
    print("This script will help you link this bot to your existing Signal account.")
    print("Requires Java and signal-cli installed.")
    
    # Check if we have any accounts
    # client_temp = SignalClient("dummy")
    # accounts = client_temp.list_accounts()
    # if accounts:
    #     print(f"Found existing accounts: {accounts}")
    #     use_existing = input("Use existing account? (y/n): ").lower()
    #     if use_existing == 'y':
    #         print("Great. Exiting.")
    #         return

    print("Generating Link URI...")
    
    # Use the client helper which handles ENV vars
    client = SignalClient("dummy")
    
    try:
        uri, process = client.get_link_uri()
        print(f"URI: {uri}")

        print("\n\n")
        print("Please scan this QR code with your Signal App (Settings -> Linked Devices -> +)")
        
        qr = qrcode.QRCode()
        qr.add_data(uri)
        qr.print_ascii()
        
        print("\nOr open this URL if you have a way to handle it:")
        print(uri)
        print("\nWaiting for device to link... (User must scan)")
        print("This script will wait until the process exits or you press Ctrl+C.")
        
        try:
             # Wait for the process to complete (it should exit after successful linking?)
             # If it doesn't exit, we might need a manual "Done" check or just let user kill it.
             # Based on some docs, `signal-cli link` keeps running?? No, usually it exits.
             # But if it outputted the URI, it's waiting for the server callback.
             process.wait()
             print("Link process finished.")
        except KeyboardInterrupt:
             print("Interrupted.")
             process.kill()
        
        print("Run `signal-cli listAccounts` or just run the bot to check if it worked.")
        
    except Exception as e:
        print(f"Error: {e}")
        return

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        import qrcode
    except ImportError:
        print("Installing qrcode library...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode"])
        import qrcode
        
    main()
