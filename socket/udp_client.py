# Import the socket library for network connections and sys for command line arguments
import socket
from sys import argv

# Define the server IP and port
ServerIP     = '127.0.0.1'
ServerPORT   = int(argv[1])  # Convert the first command line argument to an integer for the port
bufferSize   = 1024  # Define the size of the buffer for incoming messages

# Create a UDP socket
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Send a message to the server
UDPClientSocket.sendto(str.encode('Questo è il messaggio del Client'), (ServerIP, ServerPORT))

# Receive a message from the server
mess, addr = UDPClientSocket.recvfrom(bufferSize) 

# Print the message from the server, decoding it from bytes to a string
print('C: Messaggio da parte del server: {}'.format(mess.decode('utf-8')))