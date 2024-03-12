import socket
from sys import argv
import re
from threading import Thread, Lock

# Function to send data to all active connections except the sender
def sendToAll(addr, data):
    global activeConnections  # Global dictionary of active connections
    global mutex  # Global mutex for thread synchronization

    mutex.acquire()  # Acquire the lock before modifying shared resource
    for eaddr, econn in activeConnections.items():
        if not eaddr == addr:  # Don't send to the sender
            econn.sendall(data)  # Send data to econn connection
    mutex.release()  # Release the lock after modifying shared resource

# Thread function to manage each connection
def connection_manager_thread(addr, conn):
    global activeConnections  # Global dictionary of active connections
    global mutex  # Global mutex for thread synchronization

    print('Client: {}'.format(addr))  # Print the client address
    while True:
        data = conn.recv(1024)  # Receive data from the client
        if not data:  # If no data is received, break the loop
            break
        if bool(re.search('STOP', data.decode('utf-8'))):  # If the received data is a stop command, break the loop
            break
        if bool(re.search('DM', data.decode('utf-8'))):
            print('Logica di invio di messaggio privato')
            # logica di riconoscimetno {'addr': '172.0.0.1', 'port': 44444, 'msg': 'messaggio'}
            # sendToUser(daddr, msg)
            # continue
    


        print('{}: chat message: {}'.format(addr, data[:-1].decode('utf-8')))  # Print the received chat message
        
        dataToSend = '{}: {}'.format(addr, data.decode('utf-8'))  # Format the data to send

        sendToAll(addr, dataToSend.encode())  # Send the data to all connections

    mutex.acquire()  # Acquire the lock before modifying shared resource
    del activeConnections[addr]  # Remove the connection from the active connections
    mutex.release()  # Release the lock after modifying shared resource
    conn.close()  # Close the connection

if __name__ == '__main__':

    localIP     = argv[1]  # Get the local IP from command line arguments
    localPORT   = int(argv[2])  # Get the local port from command line arguments

    global activeConnections
    activeConnections = {}  # Initialize the active connections dictionary
    global mutex
    mutex = Lock()  # Initialize the mutex

    # Create a TCP server socket
    TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    TCPServerSocket.bind((localIP, localPORT))  # Bind the socket to the local IP and port
    
    try:

        while True:
            print('Chat Server UP ({},{}), waiting for connections ...'.format(localIP, localPORT))  # Print server status
            TCPServerSocket.listen()  # Listen for incoming connections
            conn, addr = TCPServerSocket.accept()  # Accept a connection

            mutex.acquire()  # Acquire the lock before modifying shared resource
            activeConnections[addr] = conn  # Add the connection to the active connections
            mutex.release()  # Release the lock after modifying shared resource
            
            # Start a new thread for the connection
            Thread(target=connection_manager_thread, args=(addr, conn),).start()

    finally:
        if TCPServerSocket:
            TCPServerSocket.close()  # Close the server socket