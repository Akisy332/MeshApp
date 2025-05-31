import socket
from datetime import datetime
import threading
from queue import Queue


message_queue = Queue(maxsize=10000)

def handle_client(conn, address):
    print("Connection from: " + str(address))
    scet = 0

    while True:
        data = conn.recv(1024).decode()
        if not data:
            break

        if data.startswith("GET_DATA"):

            response = get_new_data_from_queue()
            conn.sendall(response.encode())
        else:
            time = datetime.now()
            scet += 1
            print("from connected user: " + str(data) + " time = " + str(time) + " num_packet = " + str(scet) + "\n")


            with open("tcp_data", "a") as f:
                f.write(data + " time = " + str(time) + " num_packet = " + str(scet) + "\n")


            save_to_queue(data, time, scet)

    conn.close()

def save_to_queue(message, timestamp, packet_number):

    message_queue.put((packet_number, message, timestamp))

def get_new_data_from_queue():
    response = ""

    while not message_queue.empty():
        packet_number, message, timestamp = message_queue.get()
        response += f"{message} {packet_number}\n"

    return response if response else "No new data found.\n"

def server_program():
    host = socket.gethostname()  # get the hostname
    port = 5000  # initiate port no above 1024

    server_socket = socket.socket()  # get instance
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many clients the server can listen to simultaneously
    server_socket.listen(10)

    try:
        while True:
            conn, address = server_socket.accept()  # accept new connection
            client_thread = threading.Thread(target=handle_client, args=(conn, address))
            client_thread.daemon = True  # Set the thread as a daemon thread
            client_thread.start()
    except KeyboardInterrupt:
        print("Server is shutting down...")
    finally:
        server_socket.close()  # close the server socket

if __name__ == '__main__':
    server_program()
