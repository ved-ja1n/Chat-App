import socket
import threading
from PyQt5.QtWidgets import QApplication, QInputDialog, QDialog, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt5.QtCore import QTimer
from constants.config import *
import sys, os, keyboard, time
from ui.ui import ChatWindow

class DMWindow(QDialog):
    def __init__(self, target, send_dm_callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"DM with {target}")
        self.resize(400, 300)
        self.send_dm_callback = send_dm_callback
        self.target = target

        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)

        self.entry = QLineEdit()
        self.entry.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        layout = QVBoxLayout()
        layout.addWidget(self.chat_box)
        layout.addWidget(self.entry)
        layout.addWidget(self.send_button)

        self.setLayout(layout)

    def send_message(self):
        message = self.entry.text().strip()
        if message:
            self.send_dm_callback(self.target, message)
            self.chat_box.append(f"You -> {self.target}: {message}")
            self.entry.clear()

    def display_message(self, message):
        self.chat_box.append(message)


class ChatClient(ChatWindow):
    def __init__(self, server_ip, server_port):
        super().__init__()
        
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_addr = (server_ip, server_port)

        self.username = None
        self.socket = None
        self.connected = False
        self.message_queue = []
        self.dm_windows = {}

        self.setWindowTitle(f"Chat Client - {server_ip}:{server_port}")
        
        
        self.user_dropdown.addItem("Global Chat")
        
        self.update_server_display()
        
        # Attempt connection
        if self.connect():
            self.start_receiving()
            self.timer = QTimer()
            self.timer.timeout.connect(self.process_message_queue)
            self.timer.start(100)
            self.log_debug(f"Connected to server {server_ip}:{server_port}")
        else:
            self.log_debug("Failed to connect to server")

        self.setup_connections()

    def check_user_typing(self):
        if self.message_entry.hasFocus() and self.message_entry.text().strip():
            self.send_message(f"{IS_TYPING} {self.username}")
        else:
            self.send_message(f"{NOT_TYPING} {self.username}")

    def setup_connections(self):
        self.send_button.clicked.connect(self.send_from_main)
        self.message_entry.returnPressed.connect(self.send_from_main)
        self.open_dm_button.clicked.connect(self.open_selected_dm)
        self.change_server_button.clicked.connect(self.change_server)

    def log_debug(self, message):
        self.text_edit.append(message + "\n")
        with open('logs/log_client.txt', 'a') as file:
            file.write(message + "\n\n")

    def update_server_display(self):
        self.server_label.setText(f"{self.server_ip}:{self.server_port}")

    def change_server(self):
        ip, ok1 = QInputDialog.getText(self, "Server IP", "Enter server IP:", text=self.server_ip)
        if not ok1:
            return            
        port, ok2 = QInputDialog.getInt(self, "Server Port", "Enter server port:", value=self.server_port, min=1, max=65535)
        if not ok2:
            return
            
        # Disconnect from current server
        if self.connected:
            self.connected = False
            self.socket.close()
            
        # Connect to new server
        self.server_ip = ip
        self.server_port = port
        self.server_addr = (ip, port)
        
        if self.connect():
            self.update_server_display()
            self.start_receiving()
            self.log_debug(f"Connected to server {ip}:{port}")
        else:
            self.log_debug(f"Failed to connect to {ip}:{port}")

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(self.server_addr)
            while True:
                username, ok = QInputDialog.getText(self, "Username", "Enter your username:")
                if not ok:
                    self.socket.close()
                    return False
                self.username = username
                self.socket.send(self.username.encode(FORMAT))
                response = self.socket.recv(HEADER).decode(FORMAT)
                if response == USERNAME_ACCEPTED:
                    self.connected = True
                    self.log_debug(f"Connected as {username}")
                    return True
                elif response == USERNAME_TAKEN:
                    self.log_debug("Username already taken")
                    continue
                else:
                    self.socket.close()
                    self.log_debug("Connection failed")
                    return False
        except Exception as e:
            if self.socket:
                self.socket.close()
            self.log_debug(f"Connection error: {str(e)}")
            return False

    def start_receiving(self):
        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.check_user_typing)
        self.typing_timer.start(500)

    def receive_messages(self):
        while self.connected:
            try:
                message = self.socket.recv(HEADER).decode(FORMAT)
                if not message:
                    break
                messages = message.split("\n")
                for msg in messages:
                    if msg.startswith(f"{IS_TYPING_LIST}:") or msg.startswith("[/USERS_WHO_TYPING:]:"):
                        try:
                            users_typing = msg.split(":", 1)[1]
                            self.update_user_typing(users_typing)
                        except Exception as e:
                            self.log_debug(f"Typing update error: {str(e)}")
                        continue
                    self.message_queue.append(msg)
            except Exception as e:
                self.log_debug(f"Receive error: {str(e)}")
                break
        self.log_debug("Disconnected from server")

    def process_message_queue(self):
        while self.message_queue:
            message = self.message_queue.pop(0)
            if message.startswith(f"{USER_LIST_UPDATE}:"):
                user_list = message[len(f"{USER_LIST_UPDATE}:"):].split(',')
                if self.username in user_list:
                    user_list.remove(self.username)
                self.update_user_dropdown(user_list)
                self.log_debug(f"User list updated: {', '.join(user_list)}")
            elif message.startswith("DM "):
                self.handle_direct_message(message)
            else:
                self.display_message(message)

    def update_user_typing(self, users):
        self.typing_status.setText(f"Typing: {users}")

    def update_user_dropdown(self, user_list):
        current = self.user_dropdown.currentText()
        self.user_dropdown.clear()
        self.user_dropdown.addItem("Global Chat")
        self.user_dropdown.addItems(user_list)
        if current in user_list:
            self.user_dropdown.setCurrentText(current)
        else:
            self.user_dropdown.setCurrentText("Global Chat")

    def send_from_main(self):
        message = self.message_entry.text().strip()
        if message:
            self.send_message(message)
            self.message_entry.clear()

    def send_dm_callback(self, target, message):
        try:
            self.socket.send(f"{DM_CMD} {target} {message}".encode(FORMAT))
            self.log_debug(f"DM sent to {target}")
        except Exception as e:
            self.log_debug(f"Failed to send DM: {str(e)}")

    def send_message(self, message):
        try:
            if message.startswith(f"{DM_CMD} "):
                parts = message.split(" ", 2)
                if len(parts) < 3:
                    self.log_debug("Invalid DM format")
                    return
                recipient, msg_content = parts[1], parts[2]
                self.send_dm_callback(recipient, msg_content)
            else:
                self.socket.send(message.encode(FORMAT))
                self.log_debug("Message sent")
        except Exception as e:
            self.log_debug(f"Failed to send message: {str(e)}")

    def display_message(self, message):
        self.chat_box.append(message)

    def handle_direct_message(self, message):
        try:
            parts = message.split("]: ", 1)
            if len(parts) != 2:
                return
            sender_part = parts[0]
            if not sender_part.startswith("DM ["):
                return
            sender = sender_part[4:].strip('[]')
            if sender not in self.dm_windows:
                self.create_dm_window(sender)
            self.dm_windows[sender].display_message(message)
            self.log_debug(f"DM received from {sender}")
        except Exception as e:
            self.log_debug(f"Error handling DM: {str(e)}")

    def open_selected_dm(self):
        selected = self.user_dropdown.currentText()
        if selected != "Global Chat":
            self.create_dm_window(selected)
            self.log_debug(f"DM window opened for {selected}")

    def create_dm_window(self, target):
        if target not in self.dm_windows:
            dm_window = DMWindow(target, self.send_dm_callback)
            self.dm_windows[target] = dm_window
            dm_window.show()


if __name__ == "__main__":
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open('logs/log_client.txt', 'w') as file:
        file.write("")
    app = QApplication(sys.argv)  
    ip = input("Enter server IP: ")
    port = int(input("Enter port: "))
    client = ChatClient(server_ip=ip, server_port=port)
    client.show()
    sys.exit(app.exec())
