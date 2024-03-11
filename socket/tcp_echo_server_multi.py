# This script is a multi-threaded TCP server that echoes received messages back to the client. 
# It can handle multiple client connections simultaneously. Each client connection is managed in a separate thread. 
# The server can be stopped by sending a [STOP] command, and the echo feature can be toggled on and off by sending a [TOGGLE] command.


# Import necessary libraries
import socket
from sys import argv
import re
from threading import Thread, Lock

# This function manages each client connection
def connection_manager_thread(addr, conn):
    # Print the client address
    print('Client: {}'.format(addr))
    # Initialize toggle variable
    toggle = True
    # Infinite loop to keep the connection open
    while True:
        # Receive data from the client
        data = conn.recv(1024)
        # If no data is received, break the loop and close the connection
        if not data:
            break
        # If the received data is a STOP command, break the loop and close the connection
        if bool(re.search('STOP', data.decode('utf-8'))):
            break
        # If the received data is a TOGGLE command, flip the toggle variable
        if bool(re.search('TOGGLE', data.decode('utf-8'))):
            toggle = not toggle
        # Print the received data
        print('{}: echo message: {}'.format(addr, data[:-1].decode('utf-8')))
        # If toggle is True, echo the received data back to the client
        if toggle:
            conn.sendall(data)
    # Close the connection
    conn.close()

# Main function
if __name__ == '__main__':
    # Get the IP and port from command line arguments
    localIP     = argv[1]
    localPORT   = int(argv[2])

    # Create a TCP socket
    TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    # Bind the socket to the IP and port
    TCPServerSocket.bind((localIP, localPORT))

    # Infinite loop to keep the server running
    while True:
        # Print the server status
        print('TCP Server UP ({},{}), waiting for connections ...'.format(localIP, localPORT))
        # Listen for incoming connections
        TCPServerSocket.listen()
        # Accept a connection
        conn, addr = TCPServerSocket.accept()
        # Start a new thread for each connection
        Thread(target=connection_manager_thread, args=(addr, conn),).start()
    
    # Close the server socket
    TCPServerSocket.close()