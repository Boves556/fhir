import socket
import select
import sys
import json
import struct
from jsonschema import validate, ValidationError

HEADER_LENGTH = 4

# Sample FHIR JSON schema (simplified)
FHIR_SCHEMA = {
    "type": "object",
    "properties": {
        "resourceType": {"type": "string"},
        "id": {"type": "string"},
        "meta": {"type": "object"},
        # Add more properties based on the FHIR standard
    },
    "required": ["resourceType"]
}

# Sample user database for authentication
USER_DATABASE = {
    "Dr.Waldmann": "krankenhaus",
    "Herr.Krankwurst": "immerso",
}

def authenticate_user(auth_data):
    """Authenticate the user using the provided data."""
    username = auth_data.get("username")
    password = auth_data.get("password")
    return username in USER_DATABASE and USER_DATABASE[username] == password

def send_message(sock, message):
    """Send a message with a header indicating its length."""
    message_length = len(message)
    header = struct.pack("!I", message_length)
    sock.sendall(header + message)

def receive_message(sock):
    """Receive a message prefixed with a header indicating its length."""
    header = b""
    while len(header) < HEADER_LENGTH:
        packet = sock.recv(HEADER_LENGTH - len(header))
        if not packet:
            return None
        header += packet
    message_length = struct.unpack("!I", header)[0]
    data = b""
    while len(data) < message_length:
        packet = sock.recv(message_length - len(data))
        if not packet:
            return None
        data += packet
    return data

def validate_fhir_data(data):
    """Validate the FHIR data against the schema."""
    try:
        validate(instance=data, schema=FHIR_SCHEMA)
        return True
    except ValidationError as e:
        print(f"Invalid FHIR data: {e.message}")
        return False

def broadcast(sock, message, clients, client_names):
    """Send a message to all clients except the sender."""
    for client_socket in clients:
        if client_socket != sock:
            try:
                send_message(client_socket, message)
            except Exception as e:
                print(f"Error sending message: {e}")
                client_socket.close()
                clients.remove(client_socket)
                if client_socket in client_names:
                    leave_message = json.dumps({"type": "leave", "nick": client_names[client_socket]}).encode()
                    broadcast(client_socket, leave_message, clients, client_names)
                    del client_names[client_socket]

def chat_server(port):
    """Start the chat server and handle client connections."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", port))
    server_socket.listen(10)

    clients = []
    client_names = {}

    print(f"Chat server started on port {port}.")

    while True:
        read_sockets, _, _ = select.select([server_socket] + clients, [], [])
        for sock in read_sockets:
            if sock == server_socket:
                # Handle new client connection
                sockfd, addr = server_socket.accept()
                clients.append(sockfd)
                print(f"Client {addr} connected")
            else:
                try:
                    # Receive data from an existing client
                    data = receive_message(sock)
                    if data:
                        json_data = json.loads(data.decode())
                        if json_data["type"] == "auth":
                            # Handle authentication
                            if authenticate_user(json_data):
                                client_names[sock] = json_data["username"]
                                auth_success_message = json.dumps({"type": "auth_success"}).encode()
                                send_message(sock, auth_success_message)
                                join_message = json.dumps({"type": "join", "nick": json_data["username"]}).encode()
                                broadcast(sock, join_message, clients, client_names)
                            else:
                                auth_fail_message = json.dumps({"type": "auth_fail"}).encode()
                                send_message(sock, auth_fail_message)
                                clients.remove(sock)
                                sock.close()
                        elif json_data["type"] == "chat":
                            # Handle chat message
                            if sock in client_names:
                                broadcast_message = json.dumps({"type": "chat", "nick": client_names[sock], "message": json_data["message"]}).encode()
                                broadcast(sock, broadcast_message, clients, client_names)
                        elif json_data["type"] == "fhir":
                            # Handle FHIR data
                            if sock in client_names and validate_fhir_data(json_data["data"]):
                                broadcast_message = json.dumps({"type": "fhir", "nick": client_names[sock], "data": json_data["data"]}).encode()
                                broadcast(sock, broadcast_message, clients, client_names)
                    else:
                        # Handle client disconnection
                        if sock in clients:
                            clients.remove(sock)
                            leave_message = json.dumps({"type": "leave", "nick": client_names[sock]}).encode()
                            broadcast(sock, leave_message, clients, client_names)
                            del client_names[sock]
                except Exception as error:
                    print(f"Client disconnected: {error}")
                    sock.close()
                    if sock in clients:
                        clients.remove(sock)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server.py port")
        sys.exit()

    port = int(sys.argv[1])
    chat_server(port)
