# encoding: UTF-8

import multiprocessing
from time import sleep
from datetime import datetime, time

from vnpy.event import EventEngine2
from vnpy.trader.vtEvent import EVENT_LOG
from vnpy.trader.vtEngine import MainEngine
from vnpy.trader.gateway import ctpGateway
from vnpy.trader.app import dataRecorder

#----------------------------------------------------------------------
def printLog(content):
    """输出日志"""
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print '%s\t%s' %(t, content)
    
#----------------------------------------------------------------------
def processLogEvent(event):
    """处理日志事件"""
    log = event.dict_['data']
    if log.gatewayName:
        content = '%s:%s' %(log.gatewayName, log.logContent)
    else:
        content = '%s:%s' %('MainEngine', log.logContent)
    printLog(content)
    
#----------------------------------------------------------------------
def runChildProcess():
    """子进程运行函数"""
    print '-'*20
    printLog(u'启动行情记录运行子进程')
    
    ee = EventEngine2()
    printLog(u'事件引擎创建成功')
    
    me = MainEngine(ee)
    me.addGateway(ctpGateway)
    me.addApp(dataRecorder)
    printLog(u'主引擎创建成功')
    
    ee.register(EVENT_LOG, processLogEvent)
    printLog(u'注册日志事件监听')
    
    me.connect('CTP')
    printLog(u'连接CTP接口')
    
    while True:
        sleep(1)

#----------------------------------------------------------------------
def runParentProcess():
    """父进程运行函数"""
    printLog(u'启动行情记录守护父进程')
    
    DAY_START = time(8, 57)         # 日盘启动和停止时间
    DAY_END = time(15, 18)
    
    NIGHT_START = time(20, 57)      # 夜盘启动和停止时间
    NIGHT_END = time(2, 33)
    
    p = None        # 子进程句柄
    
    while True:
        currentTime = datetime.now().time()
        recording = False
        
        # 判断当前处于的时间段
        if ((currentTime >= DAY_START and currentTime <= DAY_END) or
            (currentTime >= NIGHT_START) or
            (currentTime <= NIGHT_END)):
            recording = True
        
        # 记录时间则需要启动子进程
        if recording and p is None:
            printLog(u'启动子进程')
            p = multiprocessing.Process(target=runChildProcess)
            p.start()
            printLog(u'子进程启动成功')
            
        # 非记录时间则退出子进程
        if not recording and p is not None:
            printLog(u'关闭子进程')
            p.terminate()
            p.join()
            p = None
            printLog(u'子进程关闭成功')
            
        sleep(5)


if __name__ == '__main__':
    runChildProcess()
    #runParentProcess()