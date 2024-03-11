# Importa i moduli necessari
import logging
import os
import time
from multiprocessing import Process

# Logica del Processo1
def process1():
    # Crea un logger chiamato 'process1'
    process1_logger = logging.getLogger('process1')
    
    # Registra l'ID del processo corrente
    process1_logger.info(f"Pid:{os.getpid()}")
    
    # Definisce il percorso del FIFO
    fifo = '/tmp/process_fifo.txt'

    # Crea un FIFO, os.mkfifo si bloccherà fino a quando non ci sarà un lettore (process2)
    os.mkfifo(fifo)

    # Apri il FIFO per la scrittura
    file = open(fifo, 'w')

    # Scrivi 10 voci nel FIFO
    for i in range(1,11):
        # Tenta di scrivere nel FIFO fino al successo
        while True:
            try:
                # Registra ogni tentativo di scrivere nel FIFO
                process1_logger.info(f"Writing {int(i)}")
                
                # Scrivi nel FIFO
                file.write(f"{i}\n")
                
                # Esegui il flush del buffer di scrittura per assicurarti che i dati siano effettivamente scritti
                file.flush()
                
                # Se la scrittura è stata eseguita con successo, interrompi il ciclo
                break
            except:
                # Se la scrittura non è stata eseguita con successo, continua il ciclo
                pass

    # Chiudi il FIFO per pulire le risorse
    file.close()

    # Tempo di cortesia per il completamento del processo di lettura
    process1_logger.info("Sleeping for 2")
    time.sleep(2)

    # Registra il completamento
    process1_logger.info("Finished process 1")

# Logica del Processo2
def process2():
    # Crea un logger chiamato 'process2'
    process2_logger = logging.getLogger('process2')
    
    # Registra l'ID del processo corrente
    process2_logger.info(f"Pid:{os.getpid()}")
    
    # Definisce il percorso del FIFO
    fifo = '/tmp/process_fifo.txt'

    # Continua a tentare di aprire il FIFO, ignora i fallimenti delle condizioni di gara
    while True:
        try:
            # Apri il FIFO per la lettura
            file = open(fifo, 'r')
            break
        except:
            pass

    # Aspetta 10 voci
    count = 0
    while count < 10:
        while True:
            try:
                # Leggi una riga dal FIFO
                line = file.readline()
                
                # Registra la riga letta
                process2_logger.info(f"Read: {int(line)}")
                
                # Incrementa il contatore
                count += 1
                break
            except:
                pass

    # Chiudi il FIFO e rimuovilo
    file.close()
    os.remove(fifo)

    # Registra il completamento
    process2_logger.info("Finished process 2")

# Funzione principale
def main():
    # Configura il logger principale e registra l'ID del processo
    parent_logger = logging.getLogger('parent')
    parent_logger.info(f"Pid:{os.getpid()}")

    # Configura i processi
    procs = [Process(target=process1), Process(target=process2)]

    # Avvia i processi
    for proc in procs:
        proc.start()

    # Aspetta che i processi terminino
    for proc in procs:
        proc.join()

# Configura un semplice logging
logging.basicConfig(level=logging.INFO)

# Esegui la funzione principale
if __name__ == '__main__':
    main()