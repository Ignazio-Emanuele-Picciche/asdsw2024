# See "Distributed Systems" - Van Steen, Tanenbaum - Ed. 4 (p. 117)

from multiprocessing import Process
from time import *
from random import *

# i processi dal punto di vista della memoria sono indipendenti, quindi non condividono le variabili

global value # variabile globale condivisa tra i processi

def sleeper(name): #, value): # value è una variabile condivisa tra i processi, ma non è una
    global value 
    t = gmtime() # tempo corrente
    value=s
    s = randint(4,20) # tempo di attesa
    txt = str(t.tm_min) + ':' + str(t.tm_sec) + ' ' + name + ' is going to sleep for ' + str(s) + ' seconds '  
    #+ str(value) 
    print(txt) # stampa il messaggio
    sleep(s) # attesa
    t = gmtime() # tempo corrente
    txt = str(t.tm_min) + ':' + str(t.tm_sec) + ' ' + name + ' has woken up ' 
    #+ str(value) 
    print(txt)

if __name__ == '__main__': # solo se è il modulo principale
    process_list = list() # lista di processi
    global value # variabile globale condivisa tra i processi
    for i in range(10): # crea 10 processi
        p = Process(target=sleeper, args=('mike_{}'.format(i),))   #, value)) # crea un processo , target è la funzione da eseguire, args sono gli argomenti della funzione
        process_list.append(p)  # aggiunge il processo alla lista

    print('tutti i processi sono pronti')

    for i, p in enumerate(process_list):  # per ogni processo nella lista
        #value = i
        p.start() # avvia il processo
        sleep(0.1) # per evitare che i processi si sovrappongano , nel caso in cui lo tolgo non c'è sincronizzazione temporale tra i processi

    print('tutti avviati')

    for p in process_list: p.join() # attende che tutti i processi terminino

    print('tutti terminati!')
