#!/usr/bin/env python
# encoding: utf-8

import os, sys, json, time, requests, shlex
import socket, threading, Queue
from threading import Thread
from optparse import OptionParser

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


def GetParas(commandstr):
    # 解析一条命令行
    try:
        opt = OptionParser()
        opt.add_option('-H', dest='headers', action='append', type=str)
        opt.add_option('-X', dest='method', type=str)
        opt.add_option('-u', dest='auth', type=str)
        opt.add_option('-d', '--data', dest='datas', type=str)
        opt.add_option("--compressed", action="store_true", dest="compressed")
        opt.add_option("--data-binary", type=str, dest="databinary")
        #
        commands = shlex.split(commandstr)
        (options, args) = opt.parse_args(commands)
        # print '>', options.headers
        # print '>>', options.databinary
        # print '>>>', args
        # print '================'
        # 返回URL以及参数列表
        return (args[1], options)

    except Exception as ex:
        print("exception :{0}".format(str(ex)))
        return None

def GetData(url, options):
    # 获取数据
    try:
        # 只处理 http 和 https 开头的协议
        if (url.lower().startswith('http://') or
            url.lower().startswith('https://')): raise Exception('unknow protocol.')
        # 解析 option 参数



    except Exception as ex:
        print("exception :{0}".format(str(ex)))
        return None


##########################################################################
if __name__ == '__main__':
    #
    print '[==DoDo==]'
    print 'Curl Download.'
    print 'Encode: %s' %  sys.getdefaultencoding()

    # https://www.cnblogs.com/emily-qin/p/6126975.html

    fname = 'test.txt'
    f = open(fname, 'r')
    text = f.read()
    f.close()
    lines = text.splitlines()
    #
    results = []
    for line in lines:
        info = GetParas(line)
        if info == None: continue
        results.append(info)

    #
    pass



    #
