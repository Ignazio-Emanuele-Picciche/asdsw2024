import socket
from sys import argv
import logging
import re
import json

# Function to decode a join command
def decodeJoin(addr, mess):
    # Use a regular expression to extract the JSON parameters from the message
    result = re.search('(\{[a-zA-Z0-9\"\'\:\.\, ]*\})' , mess)
    if bool(result):
        logging.debug('RE GROUP(1) {}'.format(result.group(1)))
        action = json.loads(result.group(1)) # Load the JSON parameters into a dictionary
    else:
        action = {} # If no parameters are found, create an empty dictionary
    
    action['command'] = 'join' # Add the command to the action dictionary

    return action

# Function to decode a leave command
def decodeLeave(addr, mess):
    # Use a regular expression to extract the JSON parameters from the message
    result = re.search('(\{[a-zA-Z0-9\"\'\:\.\, ]*\})' , mess)
    if bool(result):
        logging.debug('RE GROUP(1) {}'.format(result.group(1)))
        action = json.loads(result.group(1)) # Load the JSON parameters into a dictionary
    else:
        action = {} # If no parameters are found, create an empty dictionary
    
    action['command'] = 'leave' # Add the command to the action dictionary
    
    return action

# Function to decode a message
def decodeMessage(addr, mess):
    # Use a regular expression to extract the command from the message
    result = re.search('^\[([A-Z]*)\]' , mess)
    if bool(result):
        command = result.group(1) # Extract the command from the message
        logging.debug('COMMAND: {}'.format(command))

        '''
        if command == 'JOIN':
            decodeJoin(addr, mess)
        else if command == 'LEAVE':
            decodeLEAVE(addr, mess)
        '''

        try:
            # Use a dictionary of lambdas to call the appropriate function based on the command
            action = {
                'JOIN'  : lambda param1,param2 : decodeJoin(param1, param2), # If the command is 'JOIN', call the decodeJoin function
                'LEAVE' : lambda param1,param2 : decodeLeave(param1, param2) # If the command is 'LEAVE', call the decodeLeave function
            }[command](addr, mess) # Call the appropriate function based on the command
        except:
            action = {}
            action['command'] = 'unknown' # If the command is not recognized, set the command to 'unknown'
    else:
        action = {}
        action['command'] = 'invalid' # If no command is found, set the command to 'invalid'

    logging.debug('ACTION: {}'.format(action))

    return action

# Function to update the ring when a node joins
# Add node to the nodes list
def updateRingJoin(action, listOfNodes):
    logging.debug('RING JOIN UPDATE')
    node = {}

    # Assign an ID to the new node
    id_ = 1
    idList = [int(eNode['id']) for eNode in listOfNodes] # Create a list of node IDs
    for i in range(1, len(listOfNodes)+2):
        if i not in idList:
            id_ = i
            break
    
    # Add the new node to the list of nodes
    node['id']   = str(id_)
    node['port'] = action['port']
    node['addr'] = action['addr']

    # Check if the node already exists in the list of nodes
    nodes = [(eNode['addr'], eNode['port']) for eNode in listOfNodes]

    # Add the node to the list of nodes, if it does not already exist
    if (node['addr'], node['port']) not in nodes:
        logging.debug('OK:  Adding node {}:{}'.format(node['addr'], node['port']))
        listOfNodes.append(node)
    else:
        logging.debug('NOK: Adding node {}:{}'.format(node['addr'], node['port']))
        return False
    #
    return True

# Function to update the ring when a node leaves
def updateRingLeave(action, listOfNodes):
    logging.debug('RING LEAVE UPDATE')

    # Create a dictionary of nodes
    dictOfNodes = {eNode['id'] : eNode for eNode in listOfNodes}
    
    # Check if the node exists in the list of nodes
    if action['id'] not in dictOfNodes:
        logging.debug('NOK: Remove node {}:{}'.format(action['addr'],action['port']))
        return False

    # Select the node to remove
    nodeToRemove = dictOfNodes[action['id']]

    logging.debug('Removing node {}:{}'.format(nodeToRemove['addr'], nodeToRemove['port']))
    # Remove the node from the list of nodes
    if action['addr'] == nodeToRemove['addr'] and action['port'] == nodeToRemove['port']:
        logging.debug('OK:  Remove node {}:{}'.format(action['addr'],action['port']))
        listOfNodes.remove(nodeToRemove)
    else: # If the address and port do not match, return False
        logging.debug('NOK: Remove node {}:{}'.format(action['addr'],action['port']))
        return False
    #
    return True

# Function to update the ring based on the action
def updateRing(action, listOfNodes, oracleSocket):
    logging.info('RING UPDATE: {}'.format(action))
    
    try:
        # Use a dictionary of lambdas to call the appropriate function based on the command
        result = {
            'join'  : lambda param1,param2 : updateRingJoin(param1, param2),
            'leave' : lambda param1,param2 : updateRingLeave(param1, param2)
        }[action['command']](action, listOfNodes)
    except:
        result = False
        return result

    # Send the updated configuration to all nodes
    sendConfigurationToAll(listOfNodes, oracleSocket)
    
    return result

# Function to send the updated configuration to all nodes
def sendConfigurationToAll(listOfNodes, oracleSocket):
    N = len(listOfNodes)
    for idx, node in enumerate(listOfNodes):
        if idx == N-1: # se entro in questo controllo l'ultimo nodo si collega al primo
            nextNode = listOfNodes[0]
        else: # il prossimo nodo è idx+1
            nextNode = listOfNodes[idx + 1]

        # Send the updated configuration to the node
        addr, port = node['addr'], int(node['port'])
        message = {}
        message['id'] = node['id']
        message['nextNode'] = nextNode
        message = '[CONF] {}'.format(json.dumps(message))
        logging.debug('UPDATE MESSAGE: {}'.format(message))
        oracleSocket.sendto(message.encode(), (addr, port))

if __name__ == '__main__':

    # Get the IP and port from the command line arguments
    IP     = argv[1]
    PORT   = int(argv[2])
    bufferSize  = 1024
    listOfNodes = []

    # Set up logging
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

    # Create the socket
    oracleSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    oracleSocket.bind( (IP, PORT) )

    logging.info("ORACLE UP AND RUNNING!")

    # Main loop to receive messages and update the ring
    while True:
        mess, addr = oracleSocket.recvfrom(bufferSize)
        dmess = mess.decode('utf-8')

        logging.info('REQUEST FROM {}'.format(addr))
        logging.info('REQUEST: {}'.format(dmess))

        action = decodeMessage(addr, dmess)
        updateRing(action, listOfNodes, oracleSocket)

        logging.info('UPDATED LIST OF NODES {}'.format(listOfNodes))