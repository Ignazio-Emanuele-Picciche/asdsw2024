# from: https://github.com/spurin/python-ipc-examples
# OSS NON FUNZIONE , FIXARE

# Modalità di trasferimento di comunicazione tra processi:
# - pipe   usa risorsse esterme per mettere in collegamento i processi, some meccanismo che il sistema operativo mette a disposizione
# - coda
# - memoria condivisa

# Pipe

import logging
import os
import time
import multiprocessing
from multiprocessing import Process

# Process1 logic  # processo che scrive su un file descriptor , genra informazioni
def process1(pipe):
    process1_logger = logging.getLogger('process1') # logging è un modulo di python che permette di scrivere messaggi di log
    process1_logger.info(f"Pid:{os.getpid()}")

    # Open the file descriptor
    file = os.fdopen(pipe.fileno(), 'w')
    process1_logger.info("Opened file descriptor")

    # Write 10 entries
    for i in range(1,11): # 10 iterazioni e per ciasuna iterazone si fa un tentantivo di scrittura

        # Attempt to write to our pipe until succession
        while True:
            try:
                process1_logger.info(f"Writing {int(i)}")
                file.write(f"{i}\n")
                file.flush() # forza la scrittura e il suo invio
                if i % 6 == 0: # bloccare la scrittura , creare in buco temporale tra i processi
                    process1_logger.info("Intentionally sleeping for 5 seconds")
                    time.sleep(5)
                break
            except:
                pass

    # Clean up pipe
    pipe.close()

    # Log completion
    process1_logger.info("Finished process 1")


# Process2 logic # processo che consuma , legge le informazioni del processo 1
def process2(pipe):
    process2_logger = logging.getLogger('process2')
    process2_logger.info(f"Pid:{os.getpid()}")

    # Open the file descriptor
    file = os.fdopen(pipe.fileno(), 'r')
    process2_logger.info("Opened file descriptor")

    # Expect 10 entries
    count = 0
    while count < 10: # 10 iterazioni e per ciasuna iterazone si fa un tentantivo di lettura
        while True:
            try:
                line = file.readline()
                process2_logger.info(f"Read: {int(line)}")
                count += 1
                break
            except Exception:
                pass

    # Clean up pipe
    pipe.close() 

    # Log completion
    process2_logger.info("Finished process 2")


# Main
def main():

    # Setup parent logger and log pid
    parent_logger = logging.getLogger('parent')
    parent_logger.info(f"Pid:{os.getpid()}")

    # Setup pipe
    r, w = multiprocessing.Pipe(False) 

    # Setup processes
    procs = [Process(target=process1, args=(w,)), Process(target=process2, args=(r,))]

    # Start processes
    for proc in procs:
        proc.start()

    # Run to completion
    for proc in procs:
        proc.join()

# Setup simple logging
logging.basicConfig(level=logging.INFO)

# Execute main
if __name__ == '__main__':
    main()
