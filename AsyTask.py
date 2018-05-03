# -*- coding: utf-8 -*-

import sys, os, time
from threading import Thread
from Queue import Queue




class ThreadPoolManger():
    """线程池管理器"""
    def __init__(self, thread_num):
        # 初始化参数
        self.work_queue = Queue()
        self.thread_num = thread_num
        self.__init_threading_pool(self.thread_num)

    def __init_threading_pool(self, thread_num):
        # 初始化线程池，创建指定数量的线程池
        for i in range(thread_num):
            thread = ThreadManger(self.work_queue)
            thread.start()

    def addJob(self, func, *args):
        # 将任务放入队列，等待线程池阻塞读取，参数是被执行的函数和函数的参数
        self.work_queue.put((func, args))

    def waitDone(self):
        self.work_queue.join()

class ThreadManger(Thread):
    """定义线程类，继承threading.Thread"""
    def __init__(self, work_queue):
        Thread.__init__(self)
        self.work_queue = work_queue
        self.daemon = True

    def run(self):
        # 启动线程
        while True:
            target, args = self.work_queue.get()
            lret =target(args[0])
            if len(args) == 2:
                args[1](args[0],lret)   #callback
            self.work_queue.task_done()





def Test(tData):
    print "hello world index:%d"%tData
    time.sleep(1)

def TestDemo():
    _threadPool = ThreadPoolManger(80)
    for i in range(0,100):
        _threadPool.addJob(Test,*(i,))
    _threadPool.waitDone()


if __name__ == "__main__":
    print os.getcwd()