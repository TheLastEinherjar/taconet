import socket
import json
import threading

def relay_messages(client_socket:socket.socket) :
    global all_clients
    while True :
        message = client_socket.recv(1024)
        if len(message) > 0 :
            json_message = json.loads(message)
            if json_message['message'][0] != '-' :
                for client in all_clients :
                    try :
                        client.sendall(message)
                    except BrokenPipeError :
                        all_clients.remove(client)
            else :
                match json_message['message'] :
                    case '-close' :
                        try :
                            all_clients.remove(client_socket)
                            client_socket.close()
                        except : 
                            pass
                        for client in all_clients :
                            try :
                                client.sendall(json.dumps({'name':'<system>', 'message':f'[{json_message["name"]}] Disconected.'}).encode('utf-8'))
                            except BrokenPipeError :
                                all_clients.remove(client)



def accept_connections() :
    while True:
        # Accept a client connection
        client_socket, client_address = server_socket.accept()

        all_clients.append(client_socket)
        
        # Create a new thread to handle the client connection
        thread = threading.Thread(target=relay_messages, args=(client_socket,), daemon=True)
        
        # Start the thread
        thread.start()
        
        # Add the thread to the list of threads
        threads.append(thread)
try :
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the server socket to a specific host and port
    server_socket.bind(('0.0.0.0', 6969))

    # Get the hostname of the machine
    hostname = socket.gethostname()

    # Get the IP address associated with the hostname
    ip_address = socket.gethostbyname(hostname)

    print(f"Server is running on: {ip_address}:6969")

    # Listen for incoming connections
    server_socket.listen()

    # Create a list to store all the threads
    threads = []

    # Create a list of all clients
    all_clients = []

    acceptor_thread = threading.Thread(target=accept_connections, daemon=True)
    acceptor_thread.start()

    input("hit enter to close the server")

finally :
    # Close the server socket
    try :
        server_socket.close()
    except :
        pass