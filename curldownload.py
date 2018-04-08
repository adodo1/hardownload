#!/usr/bin/env python
# encoding: utf-8

import os, sys, json, time, requests, shlex
import socket, threading, Queue
from threading import Thread
from optparse import OptionParser
from urlparse import urlparse, urlunparse, parse_qs, parse_qsl

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
    def __init__(self, outdir, taskfile):
        self._outdir = outdir
        self._taskfile = taskfile
        self._num = 0
        self._total = 0

    def GetData(self, url, options):
        # 获取数据
        try:
            # 检查是否已经处理
            mutex.acquire()
            self._num = self._num + 1
            global _tasks
            uhash = hash((url, str(options)))     # 哈希值
            if (uhash in _tasks): return True     # 如果存在返回
            mutex.release()


            # 只处理 http 和 https 开头的协议
            if (url.lower().startswith('http://') == False and
                url.lower().startswith('https://') == False): raise Exception('unknow protocol.')
            # 解析 option 参数
            urlo = urlparse(url)
            dir1 = self.FixToPath(urlo.netloc)
            dir2 = self.FixToPath(urlo.path, False)
            dir3 = self.FixToPath(urlo.query)
            #
            if (dir2 == '' and dir3 == ''): dir1 = dir1 + '/'
            if (dir3 != ''): dir3 = '$' + dir3
            fullname = './out/' + dir1 + dir2 + dir3
            if (fullname.endswith('/')): fullname = fullname + '_index.html'
            #
            dname, fname = os.path.split(fullname)
            #print 'dir: %s | name: %s' % (dname, fname)

            if (len(fname) > 190): fname = fname[0:188]     # 文件名不能太长
            #
            index = 0
            fullname = dname + '/' + fname
            mutex.acquire()
            print '[%d/%d]: %s' % (self._num, self._total, fullname)
            while(os.path.exists(fullname)):
                index = index + 1
                fullname = '%s/%s%02d' % (dname, fname, index)
            mutex.release()

            # 用requests下载
            data = self.GetHtml(url, options)
            if (data != None):
                mutex.acquire()
                if (os.path.exists(dname) == False): os.makedirs(dname)
                f = open(fullname, 'wb')
                f.write(data)
                f.close()
                mutex.release()

            # 保存哈希并追加到任务文件中
            mutex.acquire()
            _tasks.add(uhash)
            f = open(self._taskfile, 'a')
            f.write('%s\r\n' % uhash)
            f.close()
            mutex.release()

        except Exception as ex:
            mutex.acquire()
            print("exception :{0}".format(str(ex)))
            mutex.release()
            return False

    def FixToPath(self, text, full=True):
        # 将URL中不符合命名的字符串替换掉
        text = text.replace(':', '#')
        text = text.replace('|', '+')
        text = text.replace('"', '+')
        text = text.replace('>', '+')
        text = text.replace('<', '+')
        text = text.replace('*', '+')
        text = text.replace('?', '+')
        #
        if full:
            text = text.replace('/', '+')
            text = text.replace('\\', '+')
        return text

    def GetHtml(self, url, options):
        # 处理网络请求
        headers = {}
        if (options.headers != None):
            for item in options.headers:
                index = item.find(':')
                if (index < 0): continue
                k = item[0:index].strip()
                v = item[index+1:].strip()
                headers[k] = v

        if (options.method == None or options.method == 'GET'):
            # 处理GET请求
            response = requests.get(url, headers=headers)
            data = response.content
            return data
        elif (options.method.upper() == 'POST'):
            # 处理POST请求
            response = requests.post(url, headers=headers)
            data = response.content
            return data
        else:
            # 其他方法暂时不处理
            return None

    def Work(self, resinfos, maxThreads):
        self._num = 0
        self._total = len(resinfos)
        worker = WorkerPool(maxThreads)
        for info in resinfos:
            url, options = info
            worker.add_job(self.GetData, url, options)
        worker.wait_for_complete()


def GetParas(commandstr):
    # 解析一条命令行
    try:
        if (commandstr.strip()==''): return None
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







##########################################################################
if __name__ == '__main__':
    #
    print '[==DoDo==]'
    print 'Curl Download.'
    print 'Encode: %s' %  sys.getdefaultencoding()

    # https://www.cnblogs.com/emily-qin/p/6126975.html
    outdir = './out'
    if (os.path.exists(outdir)==False):
        os.makedirs(outdir)
    # 读取任务列表
    fname = './test_more.txt'
    f = open(fname, 'r')
    text = f.read()
    f.close()
    lines = text.splitlines()
    # 最大线程
    maxThreads = 16

    # 尝试读取进度表
    global _tasks
    _tasks = set()
    tname = fname + '_.txt'
    if (os.path.exists(tname)):
        f = open(tname, 'r')
        text = f.read()
        tlines = text.splitlines()
        for line in tlines: _tasks.add(line)
    #



    #
    results = []
    for line in lines:
        info = GetParas(line)
        if info == None: continue
        results.append(info)

    #
    # spider = Spider(outdir, tname)
    # for info in results:
    #     #
    #     url, options = info
    #     spider.GetData(url, options)


    spider = Spider(outdir, tname)
    spider.Work(results, maxThreads)


    #
    print 'OK.'
