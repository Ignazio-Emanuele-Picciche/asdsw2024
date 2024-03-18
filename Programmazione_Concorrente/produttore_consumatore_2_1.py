from threading import Thread, Lock
import time
import logging
from random import randrange
from sys import argv

mutex = Lock()
sharedBuffer = [] 
produttoriRunning = 0

def safeWrite(row):
    global sharedBuffer
    global mutex

    mutex.acquire()
    sharedBuffer.append(row)
    mutex.release()

def safeRead():
    global sharedBuffer
    global mutex

    mutex.acquire()
    row = sharedBuffer[0]
    sharedBuffer.remove(row)
    mutex.release()

    return row

def thread_produttore(nome, nomefile):
    global produttoriRunning # variabile globale che indica quanti produttori sono in esecuzione

    produttoriRunning += 1 # incrementa il numero di produttori in esecuzione

        # l'aggiornamento di una variabile globale è un'operazione atomica, quindi non c'è bisogno di un mutex 
    # cos'è un'operazione atomica? è un'operazione che non può essere interrotta da un'altra operazione
    # quindi non c'è il problema che un thread possa leggere una variabile mentre un altro thread la sta modificando.


    logging.info("{} sta partendo ...".format(nome))
    #logging.info("%s sta partendo ...", nome)

# apre il file in lettura e fino a quando ci sono righe le scrive in memoria condivisa
    with open(nomefile, 'r') as f:  # apre il file in lettura e fino a quando ci sono righe le scrive in memoria condivisa
        row = f.readline() #   prende righe dai file e da degli append continui e le mette in memoria condivisa
        while row:
            safeWrite(row[:-1]) # se non metto mutex il thread consumatore potrebbe leggere la memoria condivisa mentre il produttore la sta scrivendo
            logging.info(f"{nome} ha scritto nella memoria condivisa la riga [{row[:-1]}]")
            time.sleep(randrange(2)) # attesa randomica
            row = f.readline() # legge la riga successiva

    produttoriRunning -= 1
    logging.info("{} sta terminando ...".format(nome))
    

def thread_consumatore(nome):
    global produttoriRunning 
    global sharedBuffer

    logging.info("{} sta partendo ...".format(nome))
# fin quanto c'è materiale da leggere nello shared buffer
    while produttoriRunning > 0 or len(sharedBuffer) > 0: # fin quanto c'è materiale da leggere nello shared buffer
        if len(sharedBuffer) > 0:
            row = safeRead() # legge la riga
            logging.info("{} ha letto dalla memoria condivisa la riga [{}]". format(nome, row))
        else:
            time.sleep(randrange(2,5))

    logging.info("{} sta terminando ...".format(nome))



if __name__ == "__main__":
    format = "%(asctime)s: %(message)s" # formato del messaggio di log
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")# configurazione del log

    logging.info("Main       :  before creating threads")
    # i due produttori possono avanzare l'uno dipendentemente dall'altro
    produttore1 = Thread(target=thread_produttore,  args=('Produttore1', argv[1],)) # crea un thread produtttore 1 
    produttore2 = Thread(target=thread_produttore,  args=('Produttore2', argv[2],))# crea un thread produtttore 2
    consumatore = Thread(target=thread_consumatore, args=('Consumatore',)) # crea un thread consumatore
    
    # tutti vedeono la stessa memoria condivisa , ma i due produttori ma oguno ha le propie variabili globali, 
    #le due funzioni hanno degli stoche di memoria diversi 
    # cosa sono i stache di memoria? sono delle aree di memoria che vengono allocate 
    #per le variabili locali di una funzione
    # , quando la funzione termina lo stache di memoria
    # 
    logging.info("Main       :  before running threads")

    produttore1.start()
    produttore2.start()
    consumatore.start()
    
    logging.info("Main       :  wait for the threads to finish")

    produttore1.join()
    produttore2.join()
    consumatore.join()

    logging.info("Main       :  all done")
