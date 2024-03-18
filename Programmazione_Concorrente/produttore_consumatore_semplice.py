# Import necessary libraries
from threading import Thread, Lock
import time
import logging
from random import randrange
from sys import argv

# Initialize the lock and shared buffer
mutex = Lock()
sharedBuffer = [] 
produttoreRunning = True

# Define the producer thread
def thread_produttore(nome, nomefile):
    global sharedBuffer
    global mutex
    global produttoreRunning

    logging.info("{} is starting ...".format(nome))

    # Open the file and read each line
    with open(nomefile, 'r') as f:
        row = f.readline()
        while row:
            # Acquire the lock, append the line to the shared buffer, then release the lock
            mutex.acquire()
            sharedBuffer.append(row[:-1]) # with row[:-1] remove the newline character from the end of the line
            logging.info(f"{nome} has written to the shared memory the line [{row[:-1]}]")
            mutex.release()
            # Sleep for a random amount of time between 0 and 2 seconds
            time.sleep(randrange(2))
            row = f.readline()

    # Indicate that the producer is done
    produttoreRunning = False
    logging.info("{} is finishing ...".format(nome))

# Define the consumer thread
def thread_consumatore(nome):
    global sharedBuffer
    global mutex
    global produttoreRunning

    logging.info("{} is starting ...".format(nome))

    # While the producer is still running or there is still data in the shared buffer
    while produttoreRunning or len(sharedBuffer) > 0:
        if len(sharedBuffer) > 0:
            # Acquire the lock, read and remove the first line from the shared buffer, then release the lock
            mutex.acquire()
            row = sharedBuffer[0]
            logging.info("{} has read from the shared memory the line [{}]". format(nome, row))
            sharedBuffer.remove(row)
            mutex.release()
        else:
            # Sleep for a random amount of time between 2 and 5 seconds
            time.sleep(randrange(2,5))

    logging.info("{} is finishing ...".format(nome))

# Main function
if __name__ == "__main__":
    # Set up logging
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    logging.info("Main       :  before creating threads")    
    
    # Create the producer and consumer threads
    produttore  = Thread(target=thread_produttore,  args=('Produttore', argv[1],))
    consumatore = Thread(target=thread_consumatore, args=('Consumatore',))
    
    logging.info("Main       :  before running threads")

    # Start the threads
    produttore.start()
    consumatore.start()
    
    logging.info("Main       :  wait for the threads to finish")

    # Wait for both threads to finish
    produttore.join()
    consumatore.join()

    logging.info("Main       :  all done")