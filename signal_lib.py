
import subprocess
import json
import os
import time
from typing import Generator, Optional, Dict, Any

SIGNAL_CLI_PATH = os.path.join(os.path.dirname(__file__), "signal-cli-0.13.23", "bin", "signal-cli.bat")

class SignalClient:
    def __init__(self, account: str):
        self.account = account
        self.process = None

    def _get_env(self):
        env = os.environ.copy()
        # Set JAVA_HOME if not set or invalid
        java_home = r"C:\Program Files\Java\jdk-21.0.10"
        if os.path.exists(java_home):
            env["JAVA_HOME"] = java_home
            # Ensure java bin is in PATH
            java_bin = os.path.join(java_home, "bin")
            if java_bin not in env.get("PATH", ""):
                 env["PATH"] = java_bin + os.pathsep + env.get("PATH", "")
        return env

    def send_message(self, recipient: str, message: str, attachments: list = None) -> bool:
        """Sends a message to a recipient."""
        cmd = [SIGNAL_CLI_PATH, "-a", self.account, "send", "-m", message, recipient]
        if attachments:
            for attachment in attachments:
                cmd.extend(["-a", attachment])
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._get_env())
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error sending message: {e.stderr}")
            return False

    def listen_json_rpc(self) -> Generator[Dict[str, Any], None, None]:
        """
        Starts signal-cli in JSON-RPC execution mode and yields incoming messages.
        This blocks until the process is terminated.
        """
        cmd = [SIGNAL_CLI_PATH, "-a", self.account, "--output=json", "jsonRpc"]
        
        # Start the process in a way we can read stdout continuously
        self.process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stdin=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace', # Handle emoji/unicode gracefully
            env=self._get_env()
        )

        print(f"Signal listener started for {self.account}...")

        try:
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    # Filter for incoming messages
                    if data.get("method") == "receive":
                        params = data.get("params", {})
                        envelope = params.get("envelope", {})
                        if "dataMessage" in envelope:
                             yield envelope
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON: {line[:100]}...")
        except KeyboardInterrupt:
            self.process.terminate()
        finally:
            if self.process:
                self.process.kill()

    def get_link_uri(self) -> str:
        """Helper to get the tsdevice:/?uuid=... link for linking a new device."""
        cmd = [SIGNAL_CLI_PATH, "link", "-n", "AnytypeBot"]
        
        # Use Popen to read stream in case it blocks waiting for connection
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            env=self._get_env()
        )
        
        uri = None
        try:
            # Read stdout line by line
            start_time = time.time()
            while time.time() - start_time < 10: # Wait max 10 seconds for URI
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue
                
                line = line.strip()
                if line.startswith("tsdevice:/"):
                    uri = line
                    break
        finally:
            # We found the URI or timed out. 
            # If `signal-cli link` is waiting for the user to scan, we must NOT kill it yet?
            # Wait, if we kill it, does the link expire? 
            # Usually the URI is a request to the server. The server holds the session. 
            # signal-cli might be waiting to save the session data (keys) locally.
            # If we kill signal-cli, it won't save the keys provided by the server after scanning!
            # So we typically MUST keep this process running until linked.
            pass

        if uri:
            return uri, process
        else:
            # Read stderr
            err = process.stderr.read()
            process.kill()
            raise Exception(f"Failed to get link URI: {err}")

    def list_accounts(self) -> list[str]:
        """Lists registered accounts in signal-cli"""
        # Usually signal-cli doesn't have a simple list command without config inspection,
        # but we can try to inspect the data dir. 
        # For simplicity, we assume the user knows their number or we just use the first one found in config.
        # Actually `signal-cli listAccounts` might work in newer versions or just checking data dir.
        # A robust way is checking the data directory.
        data_dir = os.path.join(os.environ.get("USERPROFILE"), ".local", "share", "signal-cli", "data")
        if not os.path.exists(data_dir):
            return []
        return [f for f in os.listdir(data_dir) if f.startswith("+")]

