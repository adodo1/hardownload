#!/usr/bin/env python
# encoding: utf-8

import os, sys, json, time, requests
import socket, threading, Queue
from threading import Thread

mutex = threading.Lock()        # 线程锁
socket.setdefaulttimeout(20)    # 连接超时

proxies = {
  #"http": "http://220.202.123.34:55336"
}

##########################################################################
class Worker(Thread):
    # thread pool, must python 2.7 up
    worker_count = 0
    def __init__(self, workQueue, resultQueue, timeout = 0, **kwds):
       Thread.__init__(self, **kwds)
       self.id = Worker.worker_count
       Worker.worker_count += 1
       self.setDaemon(True)
       self.workQueue = workQueue
       self.resultQueue = resultQueue
       self.timeout = timeout
       self.start()

    def run(self):
        ''' the get-some-work, do-some-work main loop of worker threads '''
        while True:
            try:
                callable, args, kwds = self.workQueue.get(timeout=self.timeout)
                res = callable(*args, **kwds)
                #print "worker[%2d]: %s" % (self.id, str(res))
                self.resultQueue.put(res)
            except Queue.Empty:
                break
            except :
                print 'worker[%2d]' % self.id, sys.exc_info()[:2]

class WorkerPool:
    # thread pool
    def __init__(self, num_of_workers=10, timeout = 1):
        self.workQueue = Queue.Queue()
        self.resultQueue = Queue.Queue()
        self.workers = []
        self.timeout = timeout
        self._recruitThreads(num_of_workers)
    def _recruitThreads(self, num_of_workers):
        for i in range(num_of_workers):
            worker = Worker(self.workQueue, self.resultQueue, self.timeout)
            self.workers.append(worker)
    def wait_for_complete(self):
        # ...then, wait for each of them to terminate:
        while len(self.workers):
            worker = self.workers.pop()
            worker.join()
            if worker.isAlive() and not self.workQueue.empty():
                self.workers.append(worker)
        #print "All jobs are are completed."
    def add_job(self, callable, *args, **kwds):
        self.workQueue.put((callable, args, kwds))
    def get_result(self, *args, **kwds):
        return self.resultQueue.get(*args, **kwds)


##########################################################################

class Spider:
    # 文件爬虫
    def __init__(self, outdir):
        pass

    def GetData(self, requestinfo):
        pass

    def PostData(self, requestinfo):
        pass


##########################################################################
if __name__ == '__main__':
    #
    print '[==DoDo==]'
    print 'Har Download.'
    print 'Encode: %s' %  sys.getdefaultencoding()

    # https://www.cnblogs.com/emily-qin/p/6126975.html
    fname = './test.har'
    text = open(fname, 'r').read()
    data = json.loads(text)
    entries = data['log']['entries']
    print u'总共 %d 条记录' % len(entries)



    #
