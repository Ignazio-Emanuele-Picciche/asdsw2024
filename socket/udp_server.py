# Protocollo UDP non connection oriented (non connesso)
# Basato sul concetto della "lettera"

import socket
from sys import argv

# Local IP address to which the server is bound
localIP     = '127.0.0.1'

# Local port number to which the server is bound, taken from command line arguments
localPORT   = int(argv[1])

# Size of the buffer to be used in data reception
bufferSize  = 1024

# Create a UDP socket
# AF_INET is the Internet address family for IPv4
# SOCK_DGRAM is the socket type for UDP
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Bind the socket to the local IP and port
UDPServerSocket.bind((localIP, localPORT))

print("S: UDP SERVER UP AND RUNNING!")

# Server is always listening
while True:
    # Receive message from client, also save client's address
    mess, addr = UDPServerSocket.recvfrom(bufferSize)

    # Print the received message and client's address
    print('S: Messaggio ricevuto da {}'.format(addr))
    print('S: Messaggio: {}'.format(mess.decode('utf-8')))

    # Send a response back to the client
    UDPServerSocket.sendto(str.encode('Grazie del messaggio!'), addr)
