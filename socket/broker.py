'''
Bocker:
Topic1: informazioni sulle lezioni
1 - la lezione XXXX è ritardata di 2h
2 - oggi il prof della lezione YYYY ha detto di portare il PC
...

Topic2: serata insieme
1 - andiamo a fare l'aperitivo alle 18?
2 - non mi sento bene, io rimando
...


Client:
Azioni che puo fare il client: 
1. Connessione
2. Subscribe
3. Invio messagio sul canale (Publish) 
4. Inoltro messaggi su canali sottoscritti


Conviene usare questo tipo di architettura per il tipo di comunicazione dato che questo approccio è molto piu flessibile

'''

import socket
from sys import argv
import re
from threading import Thread, Lock
import json

# Function to decode the command received from the client
def decodeCommand(message, stato):
    # Regular expressions to match the command and JSON parameters
    regexCOMMAND = r"^\[([A-Z]+)\]" # Regular expression to match a command
    regexJSON = r"(\{[\"a-zA-Z0-9\,\ \:\"\]\[]+\})" # Regular expression to match a JSON string

    # Commands that require arguments
    withArgs = {"SUBSCRIBE", "UNSUBSCRIBE", "SEND"}    

    # Extract the command from the message
    command = re.findall(regexCOMMAND, message)[0]
    comando = None

    # If a command is found, create a dictionary to hold the command and its parameters
    if command:
        comando = dict()
        comando['azione'] = command
        # If the command requires arguments and the client is connected, extract the parameters
        if command in withArgs and stato == "CONNESSO":
            stringa = re.findall(regexJSON, message)[0] # Extract the JSON string from the message
            parametri = json.loads(stringa) # Convert the JSON string to a dictionary
            comando['parametri'] = parametri 

    return comando

# Function to update the state of the connection based on the command received
def updateState(id_, stato, comando):
    global activeConnections
    global mutexACs 

    # If the client is in the pre-connection state and sends a CONNECT command, update the state to connected
    if stato == "PRE-CONNESSIONE":
        if comando['azione'] == "CONNECT":
            newStato = "CONNESSO"
            
            mutexACs.acquire()
            activeConnections[id_]['connected'] = True
            mutexACs.release()
            print('{} connected!'.format(id_))

            return newStato

    # If the client is connected and sends a DISCONNECT command, update the state to exiting
    if stato == "CONNESSO":
        if comando['azione'] == "DISCONNECT":
            newStato = "IN-USCITA"
            return newStato

    return stato

# Function to handle a SUBSCRIBE command
def subscribe(id_, conn, comando):
    global activeConnections
    global mutexACs 
    global mutexTOPICs
    global topics

    # If the command includes a topic, add the client to the list of subscribers for that topic
    if "topic" in comando['parametri']:

        topic = comando['parametri']['topic']
            
        mutexACs.acquire()
        activeConnections[id_]["topics"].add(topic)
        mutexACs.release()

        mutexTOPICs.acquire()
        if not topic in topics:
            topics[topic] = set()    
        topics[topic].add(id_)
        mutexTOPICs.release()
        print(topics)
            
        response = 'Sottoscritto al topic: {}\n'.format(topic)
        conn.sendall(response.encode())

# Function to handle an UNSUBSCRIBE command
def unsubscribe(id_, conn, comando):
    global activeConnections
    global mutexACs 
    global mutexTOPICs
    global topics

    # Remove the client from the list of subscribers for the specified topic
    topic = comando['parametri']['topic']

    mutexACs.acquire()
    activeConnections[id_]["topics"].remove(topic)
    mutexACs.release()

    mutexTOPICs.acquire()
    if topic in topics:
        if id_ in topics[topic]:
            topics[topic].remove(id_)
        if len(topics[topic]) == 0:
            del topics[topic]
    mutexTOPICs.release()
    print(topics)
    
    response = 'Cancellazione della sottoscrizione al topic: {}\n'.format(topic)
    conn.sendall(response.encode())

# Function to handle a SEND command
def send(id_, conn, comando):
    global activeConnections
    global mutexACs 
    global mutexTOPICs
    global topics

    # Send the message to all subscribers of the specified topic
    topic = comando["parametri"]["topic"]
    message = comando["parametri"]["message"]

    risposta = dict()
    risposta["id"] = id_
    risposta["topic"] = topic
    risposta["messaggio"] = message

    stringa = json.dumps(risposta) + '\n'
    print(stringa)

    mutexACs.acquire()
    mutexTOPICs.acquire()
    subscribers = topics[topic] # Lista di id dei client sottoscritti al topic
    for subID in subscribers:
        recv_conn = activeConnections[subID]["connessione"]
        recv_conn.sendall(stringa.encode())
    mutexTOPICs.release()
    mutexACs.release()

# Function to handle a DISCONNECT command
def disconnect(id_):
    global activeConnections
    global mutexACs 
    global mutexTOPICs
    global topics

    # Remove the client from all topics and delete the connection
    mutexACs.acquire()
    curr_topics = activeConnections[id_]["topics"] 
    mutexACs.release()

    mutexTOPICs.acquire()
    for topic in curr_topics:
        topics[topic].remove(id_)
        if len(topics[topic]) == 0:
            del topics[topic]
    mutexTOPICs.release()

    mutexACs.acquire()
    del activeConnections[id_]
    mutexACs.release()
    conn.close()

# Function to apply the command received from the client
def applyCommand(id_, conn, comando, stato):
    if (stato == "CONNESSO"):
        if comando['azione'] == "SUBSCRIBE":    
            subscribe(id_, conn, comando)
            return True
        if comando['azione'] == "UNSUBSCRIBE":
            unsubscribe(id_, conn, comando)
            return True
        if comando['azione'] == "SEND":
            send(id_, conn, comando)
            return True
        if comando['azione'] == "DISCONNECT":
            disconnect(id_)
            return True
    return False

# Function to manage the connection with a client
def connection_manager_thread(id_, conn):
    stato = "PRE-CONNESSIONE"               # CONNESSO, IN-USCITA
    print('Client: {}'.format(id_))

    # Loop until the client disconnects
    while not (stato == "IN-USCITA"):
        data = conn.recv(1024)
        if not data:
            break
        comando = decodeCommand(data.decode('utf-8'), stato)
        applyCommand(id_, conn, comando, stato)
        stato = updateState(id_, stato, comando)
    
if __name__ == '__main__':

    # Get the IP and port from the command line arguments
    localIP     = argv[1]
    localPORT   = int(argv[2])

    # Initialize the global variables
    global activeConnections
    activeConnections = {} # Rappresenta le connessione attive
    global mutexACs
    global mutexTOPICs
    mutexACs = Lock() # Mi serve per il controllo di accesso (active connections)
    mutexTOPICs = Lock() # Mi serve per garantire che sulla struttura dati che contiene i topics interviene un  solo thread per volta
    global topics 
    topics = dict()
    curr_id = -1

    # Create the server socket
    TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    TCPServerSocket.bind((localIP, localPORT))
    
    try:

        # Loop to accept new connections
        while True:
            print('Broker UP ({},{}), waiting for connections ...'.format(localIP, localPORT))
            TCPServerSocket.listen()                    
            conn, addr = TCPServerSocket.accept()   

            mutexACs.acquire()

            # Add the new connection to the list of active connections
            activeConnections[curr_id + 1] = {
                    'address': addr,
                    'connessione': conn,
                    'connected': False,
                    'id': curr_id + 1,
                    'topics': set()
                    }
            curr_id += 1
            
            mutexACs.release()
            
            # Start a new thread to manage the connection
            Thread(target=connection_manager_thread, args=(curr_id, conn),).start()  #
    finally:
        # Close the server socket when the program exits
        if TCPServerSocket:
            TCPServerSocket.close()
