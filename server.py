import socket
import threading
import hashlib
import os
import random
import time

CHUNK_SIZE = 1024  # 1 KB per chunk
DROP_PROBABILITY = 0.1  # 10% chance of simulating packet loss

def compute_checksum(file_path):
    """Compute SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha256.update(chunk)
    return sha256.hexdigest()

def handle_client(client_socket, client_address):
    print(f"[+] Connected to {client_address}")

    # Receive file name and size
    file_name = client_socket.recv(1024).decode()
    file_size = int(client_socket.recv(1024).decode())

    chunk = client_socket.recv(CHUNK_SIZE)
    while chunk:
        print(f"[SERVER] Received chunk of size {len(chunk)} bytes")
        f.write(chunk)
        chunk = client_socket.recv(CHUNK_SIZE)

    # Receive the file from the client
    received_data = b""
    while len(received_data) < file_size:
        data = client_socket.recv(CHUNK_SIZE)
        received_data += data

    # Save the received file
    received_file_path = f"received_{file_name}"
    with open(received_file_path, "wb") as f:
        f.write(received_data)

    print(f"[SERVER] File '{file_name}' received successfully.")

    # Compute checksum
    checksum = compute_checksum(received_file_path)
    client_socket.send(checksum.encode())  # Send checksum to client

    # Read file and send it in chunks
    with open(received_file_path, "rb") as f:
        chunks = []
        seq_num = 0

        while chunk := f.read(CHUNK_SIZE):
            chunks.append((seq_num, chunk))
            seq_num += 1

    # Shuffle chunks to simulate out-of-order transmission
    random.shuffle(chunks)

    # Send file chunks
    for seq_num, chunk in chunks:
        if random.random() > DROP_PROBABILITY:  # Simulate packet drop
            client_socket.send(f"{seq_num}".encode())  # Send sequence number
            time.sleep(0.01)  # Simulate network delay
            client_socket.send(chunk)  # Send chunk

    print(f"[SERVER] File '{file_name}' sent successfully.")

    # Handle retransmission requests
    while True:
        missing_seq = client_socket.recv(1024).decode()
        if missing_seq == "DONE":
            break

        missing_seq = int(missing_seq)
        client_socket.send(f"{missing_seq}".encode())
        time.sleep(0.01)
        client_socket.send(chunks[missing_seq][1])  # Resend missing chunk

    client_socket.close()
    print(f"[SERVER] Connection closed with {client_address}")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 5000))
    server_socket.listen(5)
    print("[SERVER] Listening on port 5000...")

    while True:
        client_socket, client_address = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

if __name__ == "__main__":
    start_server()