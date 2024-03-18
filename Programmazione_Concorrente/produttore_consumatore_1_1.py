from threading import Thread, Lock
import time
import logging
from random import randrange
from sys import argv

mutex = Lock()
sharedBuffer = [] 
produttoreRunning = True

def safeWrite(row):
    global sharedBuffer
    global mutex

    mutex.acquire() # acquisisce il mutex
    sharedBuffer.append(row) # scrive la riga nel buffer condiviso
    mutex.release()# rilascia il mutex

def safeRead():
    global sharedBuffer
    global mutex

    mutex.acquire() # acquisisce il mutex
    row = sharedBuffer[0]# legge la riga
    sharedBuffer.remove(row)# rimuove la riga dal buffer condiviso
    mutex.release() # rilascia il mutex

    return row
# due funzioni che definiscono i comportamenti dei thread
def thread_produttore(nome, nomefile):# funzione che legge un file e scrive le righe in memoria condivisa
    global produttoreRunning

    logging.info("{} sta partendo ...".format(nome)) # stampa messaggio di log
    #logging.info("%s sta partendo ...", nome)

    with open(nomefile, 'r') as f: # apre il file in lettura e fino a quando ci sono righe le scrive in memoria condivisa
        row = f.readline() # prende righe dai file e da degli append continui e le mette in memoria condivisa
        while row: # fin quando ci sono righe nel file
            safeWrite(row[:-1]) # se non metto mutex il thread consumatore potrebbe leggere la memoria condivisa mentre il produttore la sta scrivendo
            logging.info("{} ha letto dalla memoria condivisa la riga [{}]". format(nome, row[:-1])) 
            time.sleep(randrange(2)) # attesa randomica
            row = f.readline()# legge la riga successiva

    produttoreRunning = False # il produttore ha finito di scrivere
    logging.info("{} sta terminando ...".format(nome))# stampa messaggio di log

# il consumatore acede alle varibili ( quinid vede le modifiche del produttore) e legge le righe dalla memoria condivisa
def thread_consumatore(nome): # il consumatore acede alle varibili ( quinid vede le modifiche del produttore) e legge le righe dalla memoria condivisa
    global produttoreRunning 
    global sharedBuffer

    logging.info("{} sta partendo ...".format(nome))

    while produttoreRunning or len(sharedBuffer) > 0: # fin quanto c'è materiale da leggere nello shared buffer
        if len(sharedBuffer) > 0: # fin quanto c'è materiale da leggere nello shared buffer
            row = safeRead() # legge la riga
            logging.info("{} ha letto dalla memoria condivisa la riga [{}]". format(nome, row)) # stampa messaggio di log
        else:
            time.sleep(randrange(2,5)) # attesa randomica

    logging.info("{} sta terminando ...".format(nome)) 


if __name__ == "__main__":# genera due thread
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    logging.info("Main       :  before creating threads")
    
    
    produttore  = Thread(target=thread_produttore,  args=('Produttore', argv[1],))
    consumatore = Thread(target=thread_consumatore, args=('Consumatore',))
    
    logging.info("Main       :  before running threads")

    produttore.start()
    consumatore.start()
    
    logging.info("Main       :  wait for the threads to finish")

    produttore.join()
    consumatore.join()

    logging.info("Main       :  all done")
