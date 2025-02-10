import socket
import hashlib
import os

CHUNK_SIZE = 1024

def compute_checksum(file_path):
    """Compute SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha256.update(chunk)
    return sha256.hexdigest()

def start_client(file_path):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 5000))

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # Send file metadata
    client_socket.send(file_name.encode())
    client_socket.send(str(file_size).encode())

    # Send file to the server
    print(f"[CLIENT] Opening file: {file_path}")
    with open(file_path, "rb") as f:
            chunk = f.read(CHUNK_SIZE)
            while chunk:
                print(f"[CLIENT] Sending chunk of size {len(chunk)} bytes")
        # while chunk := f.read(CHUNK_SIZE):
                client_socket.send(chunk)
                chunk = f.read(CHUNK_SIZE)

    print(f"[CLIENT] File '{file_name}' sent successfully.")

    # Receive checksum from the server
    server_checksum = client_socket.recv(1024).decode()

    # Receive file chunks
    received_chunks = {}
    while True:
        try:
            seq_num = int(client_socket.recv(1024).decode())
            chunk = client_socket.recv(CHUNK_SIZE)
            received_chunks[seq_num] = chunk
        except ValueError:
            break  # All chunks received

    # Reassemble file
    received_file_path = f"reconstructed_{file_name}"
    with open(received_file_path, "wb") as f:
        for seq in sorted(received_chunks.keys()):
            f.write(received_chunks[seq])

    # Compute checksum and verify
    client_checksum = compute_checksum(received_file_path)
    if client_checksum == server_checksum:
        print("[CLIENT] Transfer successful! Checksum matched.")
    else:
        print("[CLIENT] Checksum mismatch! Requesting retransmission.")

        # Identify missing chunks
        missing_chunks = set(range(len(received_chunks))) - set(received_chunks.keys())

        for seq in missing_chunks:
            client_socket.send(str(seq).encode())  # Request missing chunk
            seq_num = int(client_socket.recv(1024).decode())
            chunk = client_socket.recv(CHUNK_SIZE)
            received_chunks[seq_num] = chunk

        # Verify again
        with open(received_file_path, "wb") as f:
            for seq in sorted(received_chunks.keys()):
                f.write(received_chunks[seq])

        client_checksum = compute_checksum(received_file_path)
        if client_checksum == server_checksum:
            print("[CLIENT] Retransmission successful! Checksum matched.")
        else:
            print("[CLIENT] Error: File is still corrupted.")

    client_socket.send("DONE".encode())  # Notify server we're done
    client_socket.close()

if __name__ == "__main__":
    file_path = input("Enter the path of the file to send: ")
    start_client(file_path)