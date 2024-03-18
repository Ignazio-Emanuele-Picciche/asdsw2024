'''
Se la metto in 127.0.0.1 posso ricevere solo richieste dalla macchina in cui mi trovo, 
se la metto in 10.0.2.15 posso ricevere sia dalla macchina in cui mi trovo che da altre macchine, ma nella stessa rete

10000 è la PORTA, il numero che serve ad identificare l'applicazione

telnet: comando che serve per instaurare una connessione tcp verso un server
'''


# Import the necessary modules
import socket
from sys import argv
import time 

# Get the IP address and port number from the command line arguments
localIP     = argv[1]
localPORT   = int(argv[2])

# Create a new socket using the AF_INET address family (IPv4) and SOCK_STREAM socket type (TCP)
TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

# Bind the socket to the specified IP address and port number
TCPServerSocket.bind((localIP, localPORT))

# Print a message indicating that the server is up and waiting for connections
print('TCP Server UP ({},{}), waiting for connections ...'.format(localIP, localPORT))

# Make the server listen for incoming connections
TCPServerSocket.listen()

# Accept a new connection from a client
# The accept() function blocks and waits for an incoming connection
# When a client connects, it returns a new socket object representing the connection and a tuple holding the address of the client
conn, addr = TCPServerSocket.accept()

# Print the address of the client that just connected
print('Client: {}'.format(addr))

# Sleep for 20 seconds
# This is likely for testing purposes, to simulate some delay or processing time
time.sleep(20)

# Enter a loop to handle the communication with the client
while True:
    # Receive data from the client
    # The recv() function blocks and waits for incoming data
    # It returns the data as a bytes object
    data = conn.recv(1024)

    # If recv() returns an empty bytes object, the client closed the connection, so break out of the loop
    if not data:
        break

    # Print the message received from the client
    print('{}: echo message: {}'.format(addr, data[:-1].decode('utf-8')))
    
    # Send the received data back to the client
    # This is what makes this server an "echo" server
    conn.sendall(data)

# Close the connection with the client
conn.close()

# Close the server socket
# After this, the server cannot accept any more connections or send/receive any more data
TCPServerSocket.close()
