import socket
import threading, os
from constants.config import *
from sql.manageSQL import add_message, load_chat
import sql.utils as serverUtil 

users_typing = []

class ChatServer:
    def __init__(self, port, host=socket.gethostbyname(socket.gethostname())):
        self.port = port
        self.host = host
        self.addr = (self.host, self.port)
        self.server_socket = None
        self.clients = {}

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(self.addr)
        self.server_socket.listen()

        print(f"Server listening on {self.host}:{self.port}")
        self.log_debug(f"Server listening on {self.host}:{self.port}")

        try:
            while True:
                conn, addr = self.server_socket.accept()
                self.log_debug(f"New connection from {addr}")
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("Server shutting down...")
            self.log_debug("Server shutting down...")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def update_user_list(self):
        user_list = list(self.clients.values())
        self.broadcast(f"{USER_LIST_UPDATE}:{','.join(user_list)}")

    def update_users_typing_list(self):
        user_typing_list = list(users_typing)
        self.broadcast(f"{IS_TYPING_LIST}:{', '.join(user_typing_list)}")

    def broadcast(self, message):
        self.log_debug(f"Broadcasting: {message}")
        disconnected_clients = []

        for client in list(self.clients.keys()):
            try:
                client.send(message.encode(FORMAT))
            except Exception:
                self.log_debug(f"Failed to send message to {self.clients.get(client, 'unknown')}")
                disconnected_clients.append(client)

        for client in disconnected_clients:
            if client in self.clients:
                del self.clients[client]

        if disconnected_clients:
            self.update_user_list()

        if not message.startswith((USER_LIST_UPDATE, IS_TYPING_LIST, f"[{IS_TYPING_LIST}:]")):
            add_message(message)

    def handle_client(self, conn, addr):
        username = self.register_username(conn)
        if not username:
            return

        self.clients[conn] = username
        self.update_user_list()

        self.log_debug(f"User {username} registered from {addr}")

        chat_history = load_chat()
        full_history = "\n".join(chat_history)
        conn.send(full_history.encode(FORMAT))

        try:
            while True:
                message = conn.recv(HEADER).decode(FORMAT)
                if not message:
                    break

                if message == DISCONNECT_MESSAGE:
                    self.log_debug(f"User {username} disconnected")
                    break

                self.process_message(conn, username, message)

        except Exception as e:
            self.log_debug(f"Error handling client {username}: {e}")
        finally:
            if conn in self.clients:
                del self.clients[conn]
            self.update_user_list()
            conn.close()
            self.log_debug(f"Connection with {username} closed")

    def register_username(self, conn):
        while True:
            try:
                username = conn.recv(HEADER).decode(FORMAT)
                if not username:
                    return None

                if username in self.clients.values():
                    conn.send(USERNAME_TAKEN.encode(FORMAT))
                else:
                    conn.send(USERNAME_ACCEPTED.encode(FORMAT))
                    return username
            except Exception as e:
                self.log_debug(f"Error during username registration: {e}")
                return None

    def process_message(self, conn, sender, message):
        words = message.strip().split()

        if len(words) >= 3 and words[0] == WHISPER_CMD:
            self.handle_whisper(conn, sender, words[1], ' '.join(words[2:]))
        elif len(words) >= 3 and words[0] == DM_CMD:
            self.handle_direct_message(conn, sender, words[1], ' '.join(words[2:]))
        elif len(words) >= 2 and words[0] == IS_TYPING:
            user = ' '.join(words[1:])
            if user not in users_typing:
                users_typing.append(user)
            self.update_users_typing_list()
        elif len(words) >= 2 and words[0] == NOT_TYPING:
            user = ' '.join(words[1:])
            if user in users_typing:
                users_typing.remove(user)
            self.update_users_typing_list()
        else:
            self.broadcast(f"[{sender}]: {message}")

    def handle_whisper(self, sender_conn, sender_name, recipient_name, message):
        if recipient_name not in self.clients.values():
            sender_conn.send(f"User {recipient_name} not found.".encode(FORMAT))
            return

        self.log_debug(f"Whisper from {sender_name} to {recipient_name}: {message}")

        for client, name in self.clients.items():
            if name == recipient_name:
                client.send(f"[Whisper from {sender_name}]: {message}".encode(FORMAT))
                sender_conn.send(f"[Whisper to {recipient_name}]: {message}".encode(FORMAT))
                break

    def handle_direct_message(self, sender_conn, sender_name, recipient_name, message):
        if recipient_name not in self.clients.values():
            sender_conn.send(f"User {recipient_name} not found.".encode(FORMAT))
            return

        self.log_debug(f"DM from {sender_name} to {recipient_name}: {message}")

        for client, name in self.clients.items():
            if name == recipient_name:
                client.send(f"DM [{sender_name}]: {message}".encode(FORMAT))
                break

    def log_debug(self, message):
        with open('logs/log_server.txt', 'a') as file:
            file.write(message + "\n\n")

def handle_cli_commands(server_instance):
    while True:
        cmd = input(">> ").strip()
        if cmd == "/list":
            print("Connected users:")
            for user in server_instance.clients.values():
                print(f"- {user}")
        elif cmd.startswith("/kick "):
            username = cmd.split(" ", 1)[1]
            for conn, user in list(server_instance.clients.items()):
                if user == username:
                    DISCONNECT_KICK_MESSAGE = "!DISCONNECT-KICK"
                    conn.send(DISCONNECT_KICK_MESSAGE.encode(FORMAT))
                    conn.close()
                    print(f"Kicked {username}")
                    break
            else:
                print("User not found.")
        elif cmd == "/abort-server":
            print("Shutting down server...")
            os._exit(0)
        elif cmd == '/clear-all' : 
            print("Purging database. A restart of the clients will be required to see the changes to take effect.")
            serverUtil.purge()
        elif cmd == '/prune' : 
            try : 
                noOfMessagesPruned = int(input("Enter the number of messages - "))
                serverUtil.prune(noOfMessagesPruned)
                print("Pruned ", noOfMessagesPruned, " messages.")
            except : 
                print("Input value must be a number.")
        else:
            print("Unknown command.")


if __name__ == "__main__":
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open('logs/log_client.txt', 'w') as file:
        file.write("")
    port = int(input("Enter server-port (user requires it for connection): "))
    server = ChatServer(port=port)
    threading.Thread(target=server.start, daemon=True).start()
    handle_cli_commands(server)  
