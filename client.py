import socket
import sys
import threading
import json
import struct

HEADER_LENGTH = 4

def send_message(sock, message):
    """Send a message with a header indicating its length."""
    message_length = len(message)
    header = struct.pack("!I", message_length)
    sock.sendall(header + message)

def receive_message(sock):
    """Continuously receive and process messages from the server."""
    while True:
        try:
            header = b""
            while len(header) < HEADER_LENGTH:
                packet = sock.recv(HEADER_LENGTH - len(header))
                if not packet:
                    print("Connection closed by the server.")
                    return
                header += packet
            message_length = struct.unpack("!I", header)[0]
            data = b""
            while len(data) < message_length:
                packet = sock.recv(message_length - len(data))
                if not packet:
                    print("Connection closed by the server.")
                    return
                data += packet
            message = json.loads(data.decode())
            if message["type"] == "auth_success":
                print("Authentication successful!")
            elif message["type"] == "auth_fail":
                print("Authentication failed. Disconnecting...")
                return
            elif message["type"] == "chat":
                print(f"{message['nick']}: {message['message']}")
            elif message["type"] == "join":
                print(f"*** {message['nick']} has joined the chat")
            elif message["type"] == "leave":
                print(f"*** {message['nick']} has left the chat")
            elif message["type"] == "fhir":
                print(f"FHIR data from {message['nick']}: {json.dumps(message['data'], indent=2)}")
        except socket.timeout:
            continue  # Ignore timeout errors and try again
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

def chat_client(username, password, host, port):
    """Start the chat client, handle authentication and user input."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)

    # Connect to remote host
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"Unable to connect: {e}")
        sys.exit()

    # Send authentication message
    auth_message = json.dumps({"type": "auth", "username": username, "password": password}).encode()
    send_message(sock, auth_message)

    # Start a thread to receive messages
    threading.Thread(target=receive_message, args=(sock,)).start()

    # Handle user input
    while True:
        msg = input(username + "> ")
        if msg == "/q":
            break
        elif msg.startswith("/fhir "):
            try:
                fhir_data = json.loads(msg[6:])
                fhir_message = json.dumps({"type": "fhir", "data": fhir_data}).encode()
                send_message(sock, fhir_message)
            except json.JSONDecodeError:
                print("Invalid FHIR JSON data.")
        else:
            chat_message = json.dumps({"type": "chat", "message": msg}).encode()
            send_message(sock, chat_message)

    # Close the socket when done
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python chat_client.py username password host port")
        sys.exit()

    # Get user inputs from command-line arguments
    username = sys.argv[1]
    password = sys.argv[2]
    host = sys.argv[3]
    port = int(sys.argv[4])
    chat_client(username, password, host, port)
