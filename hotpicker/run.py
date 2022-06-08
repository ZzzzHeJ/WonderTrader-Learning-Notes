import pandas as pd
import datetime as dt
from wtpy.apps import WtCacheMonExchg, WtCacheMonSS, WtMailNotifier
from RqCacheMonExchg import RqCacheMonExchg
import datetime
import logging
import os
import sys
os.chdir(sys.path[0])

logging.basicConfig(filename='hotsel.log', level=logging.INFO, filemode="w", 
    format='[%(asctime)s - %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
# 设置日志打印格式
formatter = logging.Formatter(fmt="[%(asctime)s - %(levelname)s] %(message)s", datefmt='%m-%d %H:%M:%S')
console.setFormatter(formatter)
# 将定义好的console日志handler添加到root logger
logging.getLogger('').addHandler(console)

def rebuild_hot_rules(hotFile = "hots.json",secFile="seconds.json",start_date=None,end_date=None):
    '''
    重构全部的主力合约切换规则
    '''
    # 从交易所官网拉取行情快照
    # cacher = WtCacheMonExchg()
    cacher = RqCacheMonExchg(start_date,end_date,"rq_daily_cache.pkl") 

    # 从datakit落地的行情快照直接读取
    # cacher = WtCacheMonSS("./FUT_DATA/his/snapshot/")

    picker = hotpicker.WtHotPicker(hotFile=hotFile, secFile=secFile)
    picker.set_cacher(cacher)

    sDate = start_date
    eDate = None # 可以设置为None，None则自动设置为当前日期
    hotRules,secRules = picker.execute_rebuild(sDate, eDate, wait=True)
    print(hotRules)
    print(secRules)

def daily_hot_rules(hotFile = "hots.json",secFile="seconds.json",start_date=None,end_date=None):
    '''
    增量更新主力合约切换规则
    '''

    cacher = RqCacheMonExchg(start_date,end_date,"rq_daily_cache.pkl")  

    # 从datakit落地的行情快照直接读取
    # cacher = WtCacheMonSS("./FUT_DATA/his/snapshot/")

    picker = hotpicker.WtHotPicker(hotFile=hotFile, secFile=secFile)
    picker.set_cacher(cacher)

    # notifier = WtMailNotifier(user="yourmailaddr", pwd="yourmailpwd", host="smtp.exmail.qq.com", port=465, isSSL=True)
    # notifier.add_receiver(name="receiver1", addr="receiver1@qq.com")
    # picker.set_mail_notifier(notifier)

    eDate = datetime.datetime.strptime("2016-03-01", '%Y-%m-%d') # 可以设置为None，None则自动设置为当前日期
    picker.execute_increment(eDate)
    
if __name__ == '__main__':
    
    root = r".\common"
    start_date = dt.datetime(2010,1,1)
    end_date = None
    
    hotFile = "hots.json"
    secFile = "seconds.json"
    rebuild_hot_rules(os.path.join(root,hotFile),os.path.join(root,secFile),start_date,end_date)
 