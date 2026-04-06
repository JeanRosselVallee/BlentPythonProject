import time
import random
from threading import Thread

def thread_f(index):
    print(f"Thread {index}: start")
    sleep = round(random.random() * 2, 1)
    time.sleep(sleep)
    print(f"Thread {index}: end after {sleep}s.")
    return sleep
class ThreadWithReturnValue(Thread):    
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super().__init__(group=group, name=name)
        self._target = target
        self._args = args
        self._kwargs = kwargs
        self._return = None
    def run(self):
        self._return = self._target() 
    def join(self):
        super().join()
        return self._return

def gather_threads(targets):
    results=[-1] * len(targets)
    print("gather_threads: start")
    # Define Threads
    threads = [ ThreadWithReturnValue(target=t) for t in targets ]
    # Launch All Threads
    for thread in threads:
        thread.start()
    # Get Results
    for i, thread in enumerate(threads):
        results[i] = thread.join() # stops if thread in progress
    print("gather_threads: end")
    return results
targets = [ ( lambda x=i: thread_f(x) ) for i in range(10) ]
results = gather_threads(targets)
print("Temps maximum attendu : {:2.1f}s".format(max(results)))