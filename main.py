import socket
import threading

# List of allowed IP addresses
allowed_ips = ['10.6.100.132', '10.6.100.130','10.6.100.131','10.1.34.55']  # Add your allowed IPs here

def handle_client(client_socket):
    client_address = client_socket.getpeername()[0]  # Get the client's IP address

    if client_address in allowed_ips:
        request = client_socket.recv(4096)
        first_line = request.split(b'\r\n')[0]
        method, address, _ = first_line.split(b' ')

        if method == b'CONNECT':
            host_port = address.decode()  # The address contains only the host
            host, port = host_port.split(':')
            remote_port = int(443)  # HTTPS port
            print("HTTPS", host, str(port))

            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((host, remote_port))

            client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')

            def forward_traffic(source, destination):
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.send(data)

            threading.Thread(target=forward_traffic, args=(client_socket, remote_socket)).start()
            threading.Thread(target=forward_traffic, args=(remote_socket, client_socket)).start()
        else:
            # Extract the requested URL from the address
            url = address.decode()
            host = url.split('/')[2]  # Extract the hostname from the URL

            print("HTTP", url)

            # Create a socket to connect to the remote server
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((host, 80))  # Using port 80 for HTTP

            # Forward the client's request to the remote server
            remote_socket.send(request)

            # Receive the response from the remote server
            remote_response = remote_socket.recv(4096)

            # Forward the remote server's response to the client
            client_socket.send(remote_response)

            # Close the sockets
            remote_socket.close()
            client_socket.close()
    else:
        print(f"Connection from {client_address} not allowed. Closing connection.")
        client_socket.close()

def run_proxy_server(port):
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind(('0.0.0.0', port))
    proxy_socket.listen(5)

    print(f"Proxy server running on port {port}")

    while True:
        client_socket, _ = proxy_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    proxy_port = 8080  # You can change this to any available port
    run_proxy_server(proxy_port)
