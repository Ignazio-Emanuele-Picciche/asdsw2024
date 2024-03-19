from cmd import Cmd
from threading import Thread
from sys import argv
import time 
import os
import re
import socket
import logging
import json

def sendDataToRing(clientSocket, nextNode, idSorgente, idDestinazione, mess):
    # Create a dictionary to hold the message data
    messaggio = {}
    # Set the source ID of the message
    messaggio['idSorgente'] = idSorgente
    # Set the destination ID of the message
    messaggio['idDestinazione'] = idDestinazione
    # Set the payload of the message
    messaggio['payload'] = mess

    # Convert the message dictionary to a JSON string and prepend it with '[DATA] '
    stringaMessaggio = '[DATA] {}'.format(json.dumps(messaggio))
    # Log the message that is about to be sent
    logging.debug('Invio Messaggio: {}'.format(stringaMessaggio))

    # Get the address and port of the next node in the ring
    nextNodeAddress = nextNode['addr']
    nextNodePort    = int(nextNode['port'])
    # Send the message to the next node in the ring
    clientSocket.sendto(stringaMessaggio.encode(), (nextNodeAddress, nextNodePort))


class RingPrompt(Cmd): # Command Line Interface, classe base per la gestione di un prompt
    # Set the command prompt and introduction message
    prompt = ''
    intro  = 'Benvenuto nel ring. Usa ? per accedere all\'help'

    # Configure the socket, next node, and source ID
    def conf(self, socket, nextNode, idSorgente):
        self.socket = socket
        self.nextNode = nextNode
        self.idSorgente = idSorgente

        # Set the prompt to show the source ID and next node ID
        self.prompt = '[{}-->{}]>'.format(idSorgente, nextNode['id'])

    # Exit the command prompt
    def do_exit(self, inp):
        print('Ciao, alla prossima!')
        return True

    # Send a message to another node
    def do_send(self, inp):
        # Message prototype: send [id] <MESSAGE>
        result = re.search('^\[([0-9]*)\]', inp)
        if bool(result):
            idDestinazione = result.group(1)
        result = re.search('<([a-zA-Z0-9\,\.\;\'\"\!\?<> ]*)>', inp)
        if bool(result):
            mess = result.group(1)
        logging.debug('SENDING MESSAGE:\nRecipient: {}\nMessage: {}'.format(idDestinazione, mess))
        
        # Send the message to the next node in the ring
        sendDataToRing(self.socket, self.nextNode, self.idSorgente, idDestinazione, mess)

    # Print a received message
    def echo_message(self, inp):
        print('Received Message: {}'.format(inp))

    # Execute a shell command and print the output
    def do_shell(self, inp):
        print(os.popen(inp).read())

def managePrompt(prompt):
    # Start the command loop for the prompt
    # This will keep the prompt open until the user exits
    prompt.cmdloop()

def join(clientSocket, currNode, nextNode, oracleIP, oraclePORT):
    # Create a join message with the current node's information
    mess = '[JOIN] {}'.format(json.dumps(currNode))
    logging.debug('JOIN MESSAGE: {}'.format(mess))
    # Send the join message to the oracle
    clientSocket.sendto(mess.encode(), (oracleIP, oraclePORT))
    # Receive a response from the oracle
    mess, addr = clientSocket.recvfrom(1024)
    mess = mess.decode('utf-8')
    logging.debug('RESPONSE: {}'.format(mess))
    
    # Search for a JSON object in the response
    result = re.search('(\{[a-zA-Z0-9\"\'\:\.\,\{\} ]*\})', mess)
    if bool(result):
        logging.debug('RE GROUP(1) {}'.format(result.group(1)))	
        # Parse the JSON object from the response
        action = json.loads(result.group(1))
        # Update the current node's ID
        currNode['id'] = action['id']
        # Update the next node's ID, address, and port
        nextNode['id'] = action['nextNode']['id']
        nextNode['addr'] = action['nextNode']['addr']
        nextNode['port'] = action['nextNode']['port']
        logging.debug('NEW CONF: \n\t currNode: {} \n\t nextNode: {}'.format(currNode, nextNode))
    else:
        action = {}

def leave(clientSocket, currNode, oracleIP, oraclePort):
    # Create a leave message with the current node's information
    mess = '[LEAVE] {}'.format(json.dumps(currNode))
    logging.debug('LEAVE MESSAGE: {}'.format(mess))
    # Send the leave message to the oracle
    clientSocket.sendto(mess.encode(), (oracleIP, oraclePort))

def sendMessage(clientSocket, nextNode, message):
    # This function is currently a placeholder and does not perform any actions
    pass

def updateConfiguration(clientSocket, currNode, nextNode, mess, prompt):
    logging.debug('UPDATE CONFIGURATION')

    # Search for a JSON object in the message
    result = re.search('(\{[a-zA-Z0-9\"\'\:\.\,\{\} ]*\})', mess)
    if bool(result):
        # Parse the JSON object from the message
        configuration = json.loads(result.group(1))
        logging.debug('NEW CONFIGURATION: {}'.format(configuration))
        # Update the current node's ID
        currNode['id'] = configuration['id']
        # Update the next node's ID, address, and port
        nextNode['id'] = configuration['nextNode']['id']
        nextNode['addr'] = configuration['nextNode']['addr']
        nextNode['port'] = configuration['nextNode']['port']
        # Reconfigure the prompt with the new next node and current node ID
        prompt.conf(clientSocket, nextNode, currNode['id'])
    
def decodeData(clientSocket, currNode, nextNode, mess, prompt):
    logging.debug('DATA MESSAGE')
    # Search for a JSON object in the message
    result = re.search('(\{[a-zA-Z0-9\"\'\:\.\,\{\} ]*\})', mess)
    if bool(result):
        # Parse the JSON object from the message
        message = json.loads(result.group(1))
        logging.debug('NEW MESSAGE: {}'.format(message))
        # Extract the source ID, destination ID, and payload from the message
        idSorgente = message['idSorgente']
        idDestinazione = message['idDestinazione']
        payload = message['payload']
        # If the destination ID matches the current node's ID, print the message
        if idDestinazione == currNode['id']:
            prompt.echo_message('{}->{}: {}'.format(idSorgente, idDestinazione, payload))
        # If the source ID matches the current node's ID, drop the message
        elif idSorgente == currNode['id']:
            logging.debug('DROPPING MESSAGE')
        # Otherwise, forward the message to the next node
        else:
            addr = nextNode['addr']
            port = int(nextNode['port'])
            clientSocket.sendto(mess.encode(), (addr, port))


def receiveMessage(clientSocket, currNode, nextNode, prompt):
    # Receive a message from the client socket
    mess, addr = clientSocket.recvfrom(1024)
    mess = mess.decode('utf-8')
    logging.debug('MESSAGE FROM {}:{} = {}'.format(addr[0], addr[1], mess))

    action = False

    # Search for a command at the start of the message
    result = re.search('^\[([A-Z]*)\]', mess)
    if bool(result):
        command = result.group(1)
        # If the command is 'CONF' or 'DATA', execute the corresponding function
        if command in {'CONF', 'DATA'}:
            action = {
                'CONF' : lambda param1, param2, param3, param4, param5 : updateConfiguration(param1, param2, param3, param4, param5),
                'DATA' : lambda param1, param2, param3, param4, param5 : decodeData(param1, param2, param3, param4, param5)
            }[command](clientSocket, currNode, nextNode, mess, prompt)

    return action

if __name__ == '__main__':

    # Get the oracle IP and port, and the client IP and port from the command line arguments
    oracleIP     = argv[1]
    oraclePORT   = int(argv[2])
    clientIP     = argv[3]
    clientPORT   = int(argv[4])

    # Set up logging
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.ERROR)

    # Create a UDP socket and bind it to the client IP and port
    clientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    clientSocket.bind( (clientIP, clientPORT) )

    logging.info('CLIENT UP AND RUNNING')

    # Initialize the current node and next node dictionaries
    currNode = {}
    nextNode = {}

    # Set the current node's address and port
    currNode['addr'] = clientIP
    currNode['port'] = str(clientPORT)

    # Send a join request to the oracle
    join(clientSocket, currNode, nextNode, oracleIP, oraclePORT)
    logging.debug('NEW CONFIGURATION:\n\t{}\n\t{}'.format(currNode, nextNode))

    # Create a new RingPrompt and configure it with the client socket, next node, and current node ID
    prompt = RingPrompt()
    prompt.conf(clientSocket, nextNode, currNode['id'])

    # Start a new thread to manage the prompt
    Thread(target=managePrompt, args=(prompt,)).start()

    # Main loop for receiving messages
    while True:
        receiveMessage(clientSocket, currNode, nextNode, prompt)