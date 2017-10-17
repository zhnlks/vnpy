# encoding: UTF-8

import multiprocessing
from time import sleep
from datetime import datetime, time

from vnpy.event import EventEngine2
from vnpy.trader.vtEvent import EVENT_LOG
from vnpy.trader.vtEngine import MainEngine
from vnpy.trader.gateway import ctpGateway
from vnpy.trader.app import ctaStrategy
from vnpy.trader.app.ctaStrategy.ctaBase import EVENT_CTA_LOG

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
def processCtaLogEvent(event):
    """处理CTA模块日志事件"""
    log = event.dict_['data']
    content = '%s:%s' %('CTA Engine', log.logContent)
    printLog(content)
    
#----------------------------------------------------------------------
def runChildProcess():
    """子进程运行函数"""
    print '-'*20
    printLog(u'启动CTA策略运行子进程')
    
    ee = EventEngine2()
    printLog(u'事件引擎创建成功')
    
    me = MainEngine(ee)
    me.addGateway(ctpGateway)
    me.addApp(ctaStrategy)
    printLog(u'主引擎创建成功')
    
    ee.register(EVENT_LOG, processLogEvent)
    ee.register(EVENT_CTA_LOG, processCtaLogEvent)
    printLog(u'注册日志事件监听')
    
    me.connect('CTP')
    printLog(u'连接CTP接口')
    
    sleep(5)    # 等待CTP接口初始化
    
    cta = me.appDict[ctaStrategy.appName]
    
    cta.loadSetting()
    printLog(u'CTA策略载入成功')
    
    cta.initAll()
    printLog(u'CTA策略初始化成功')
    
    cta.startAll()
    printLog(u'CTA策略启动成功')
    
    while True:
        sleep(1)

#----------------------------------------------------------------------
def runParentProcess():
    """父进程运行函数"""
    printLog(u'启动CTA策略守护父进程')
    
    DAY_START = time(8, 45)         # 日盘启动和停止时间
    DAY_END = time(15, 30)
    
    NIGHT_START = time(20, 45)      # 夜盘启动和停止时间
    NIGHT_END = time(2, 45)
    
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
    
    # 尽管同样实现了无人值守，但强烈建议每天启动时人工检查，为自己的PNL负责
    # runParentProcess()