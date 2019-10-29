import numpy as np
import sys
import random
import time
from mpi4py import MPI

def behavior(rank,forks,Greedy): #Behave as a friendly or greedy philosopher
    if (rank == data[size]) or (rank == data[size-1]):
        Greedy = True
    return Greedy

def getGreedy(size): #Function to decide which philosophers are going to be greedy ones by their rank
    ran = random.randint(1,size-1)
    ran2 = ran
    while ran2 == ran:
        ran2 = random.randint(1,size-1)
    return ran, ran2

def forkCheck(leftFork,rightFork,forks,rank): #Check if forks are available
    if (leftFork == True) and (rightFork == False):
        (rightFork, forks) = checkRight(rightFork,forks,rank)
        if (rightFork == False) and Greedy == False:
            leftFork = False
            forks[rank-1] = 0

    if leftFork == False:
        (leftFork, forks) = checkLeft(leftFork,forks,rank)
        if leftFork == True:
            (rightFork,forks) = checkRight(rightFork,forks,rank)
    return leftFork, rightFork, forks

def checkLeft(leftFork,forks,rank): #Check left fork
    if forks[rank-1] == 0: 
            leftFork = True
            forks[rank-1] = rank
    return leftFork, forks

def checkRight(rightFork,forks,rank): #Check right fork
    if forks[rank % (size-1)] == 0:
        rightFork = True
        forks[rank % (size-1)] = rank
    return rightFork, forks

def processSleep(wait,time): #Sleep
    while wait > 0:
        if MPI.Wtime()-time >=1:
            time = MPI.Wtime()
            wait-=1

def printPhilosophers(rank,data): #Output
    left = ("|     x     ")
    right =  ("|     x     |")
    leftfree = ("|           ")
    rightfree = ("|           |")
    available = ("|           x           |")
    notavailable = ("|                       |")
    x1 = ("-"*25)
    x2 = ("|      Philosopher "+str(rank)+"       |")
    if (rank == greedy1) or (rank == greedy2):
        x3 = ("|       (Greedy)        |")
    else:
        x3 = ("|                       |")
    x4 = ("-"*25)
    if data[rank-1] == rank:
        x5 = left
    else:
        x5 = leftfree
    if data[rank % (size-1)] == rank:
        x5 += right
    else:
        x5 += rightfree
    x6 = ("-"*25)
    if (data[rank-1] != rank) and (data[rank % (size-1)] != rank):
        x7 = available
    else:
        x7 = notavailable
    x8 = ("-"*25)
    return (x1,x2,x3,x4,x5,x6,x7,x8)

def rootPrint(data,size): #Output
    show = np.empty(shape=(8,),dtype=object) #20 = size-1

    (show[0],show[1],show[2],show[3],show[4],show[5],show[6],show[7]) = printPhilosophers(1,data)

    for x in range(2,size): #14 = size-1
        (x1,x2,x3,x4,x5,x6,x7,x8) = printPhilosophers(x,data)
        show[0] += x1
        show[1] += x2
        show[2] += x3
        show[3] += x4
        show[4] += x5
        show[5] += x6
        show[6] += x7
        show[7] += x8

    for x in range(0,8):
        print(show[x])

world_comm = MPI.COMM_WORLD
size = world_comm.Get_size()

node_comm = world_comm.Split_type(MPI.COMM_TYPE_SHARED)
rank = node_comm.rank

disp_unit = MPI.INT.Get_size()
k = int(sys.argv[1]) #Number of times the philosophers will execute the tasks
(greedy1, greedy2) = getGreedy(size) #Greedy philosophers

data = np.empty(shape=(1,),dtype='i') #Forks array

data[0] = 0
for x in range (1,size-1):
    data = np.append(data,[0],axis=0)

if rank != 0:
    data = np.append(data,[1],axis=0)
    data = np.append(data,[1],axis=0)
    data = np.append(data,[1],axis=0)

leftFork = False
rightFork = False
Greedy = False
Finish = False

if rank == 0:
    memory_size = disp_unit
else:
    memory_size = 0

win = MPI.Win.Allocate_shared(memory_size, disp_unit, comm=node_comm)
veces = 0
init = 0

if rank == 0:
    data = np.append(data,[greedy1],axis=0)
    data = np.append(data,[greedy2],axis=0)
    data = np.append(data,0)
    win.Put(data,0)

start = MPI.Wtime()
node_comm.barrier()
while True:
    sys.stdout.flush()
    
    if (leftFork == True) and (rightFork == False) and (Greedy == False):
        i = random.randint(5,15)
        actual = MPI.Wtime()
        processSleep(i,actual)
    

    win.Lock(MPI.LOCK_EXCLUSIVE, 1)   ####Lock
    win.Get(data, 0)

    if init == 0:
        Greedy = behavior(rank,data,Greedy)
        init = 1

    if rank != 0:
        (leftFork, rightFork, data) = forkCheck(leftFork,rightFork,data,rank)
        #print(data)

    win.Put(data, 0)
    win.Unlock(1)                     #####Unlock

    if (rank==0) and (MPI.Wtime()-start >= 1):
        rootPrint(data,size)
        start = MPI.Wtime()

    if (leftFork == True) and (rightFork == True):
        actual = MPI.Wtime()
        i = random.randint(7,10)
        processSleep(i,actual)
        actual = MPI.Wtime()
        i = random.randint(2,5)
        processSleep(i,actual)

    win.Lock(MPI.LOCK_EXCLUSIVE, 1) #####Lock
    win.Get(data, 0)
    if (leftFork == True) and (rightFork == False) and (Greedy == False):
            leftFork = False
            data[rank-1] = 0
    if (leftFork == True) and (rightFork == True):
        data[rank-1] = 0
        data[rank % (size-1)] = 0
    if Finish == True:
        data[size+1] +=1
    win.Put(data, 0)
    win.Unlock(1)                   #####Unlock
    
    if (leftFork == True) and (rightFork == True):
        actual = MPI.Wtime()
        i = random.randint(7,10)
        processSleep(i,actual)

    if Finish == True: break

    if (leftFork == True) and (rightFork == True):
        leftFork = False
        rightFork = False
        veces+=1
        if (veces >= k):
            Finish = True

    if (rank == 0) and (data[size+1] == size-1):
        Finish = True