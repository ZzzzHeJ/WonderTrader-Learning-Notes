from wtpy.apps import WtCacheMon
import rqdatac as rq
import datetime
import urllib
import pandas as pd
from tqdm import tqdm

import urllib.request
import io
import gzip
import xml.dom.minidom
from pyquery import PyQuery as pq
import re
import json
import pickle
import os
rq.init()
class DayData:
    '''
    每日行情数据
    '''

    def __init__(self):
        self.pid = ''
        self.month = 0
        self.code = ''  # 代码
        self.close = 0  # 今收盘(收盘价)
        self.volume = 0  # 成交量(手)
        self.hold = 0  # 空盘量(总持？持仓量)

def httpGet(url, encoding='utf-8'):
    request = urllib.request.Request(url)
    request.add_header('Accept-encoding', 'gzip')
    request.add_header(
        'User-Agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')
    try:
        f = urllib.request.urlopen(request)
        ec = f.headers.get('Content-Encoding')
        if ec == 'gzip':
            cd = f.read()
            cs = io.BytesIO(cd)
            f = gzip.GzipFile(fileobj=cs)

        return f.read().decode(encoding)
    except:
        return ""
    
def httpPost(url, datas, encoding='utf-8'):
    headers = {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
        'Accept-encoding': 'gzip'
    }
    data = urllib.parse.urlencode(datas).encode('utf-8')
    request = urllib.request.Request(url, data, headers)
    try:
        f = urllib.request.urlopen(request)
        ec = f.headers.get('Content-Encoding')
        if ec == 'gzip':
            cd = f.read()
            cs = io.BytesIO(cd)
            f = gzip.GzipFile(fileobj=cs)

        return f.read().decode(encoding)
    except:
        return ""
    
class RqCacheMonExchg(WtCacheMon):
    '''
    米筐数据缓存器
    '''
    
    def __init__ (self,start_date,end_date,pkl_file=""):
        super().__init__()
        self.pkl_file = pkl_file
        self.all_info = rq.all_instruments("Future")
        self.all_info = self.all_info[(self.all_info["listed_date"]!="0000-00-00") & (self.all_info["de_listed_date"]!="0000-00-00")]
        self.all_info["listed_date"] = pd.to_datetime(self.all_info["listed_date"])
        self.all_info["de_listed_date"] = pd.to_datetime(self.all_info["de_listed_date"])
        if start_date == None:
            start_date = self.all_info["listed_date"].min()
        if end_date == None:
            end_date = self.all_info["de_listed_date"].max()
        self.all_info = self.all_info[(self.all_info["de_listed_date"] > start_date) & (self.all_info["listed_date"] < end_date)]
        self.init_cache()
        self.all_info = self.all_info.set_index("order_book_id")
    def init_cache(self):
        try:
            with open(self.pkl_file,"rb") as f:
                self.day_cache = pickle.load(f)
        except:
            pass
        # 过滤已有的数据
        loaded_date = {}
        for key,value in self.day_cache.items():
            for exchg,item in value.items():
                for comm in item.keys():
                    loaded_date[comm.upper()] = max(datetime.datetime.strptime(key,"%Y%m%d"),loaded_date.get(comm,datetime.datetime(1996,1,1)))
        exchgs = ["CFFEX","SHFE","DCE","CZCE","INE"]
        df = self.all_info[self.all_info["exchange"].isin(exchgs)]
        now = datetime.datetime.now()
        for exchg in exchgs:
            df = self.all_info[self.all_info["exchange"] == exchg]
            comms = set()
            for index,row in df.iterrows():
                comm = row["order_book_id"]
                de_listed_date = row["de_listed_date"]
                last_loaded = loaded_date.get(comm,datetime.datetime(1996,1,1))
                if (de_listed_date > last_loaded) and (now.date() > last_loaded.date()):
                    comms.add(comm)
            if len(comms) == 0:
                continue
            data = rq.get_price(comms,start_date = df["listed_date"].min(),end_date=df["de_listed_date"].max(),frequency="1d")
            for index,row in tqdm(data.iterrows(),desc=exchg,total=len(data)):
                dtStr = index[1].strftime('%Y%m%d')
                code = index[0]
                month = re.search("(\d+)",code)[0]
                pid = re.search("[a-zA-Z]+",code)[0]
                item = DayData()
                if exchg in ["CZCE","CFFEX"]:
                    pid = pid.upper()
                    if exchg == "CZCE":
                        month = month[-3:]
                else:
                    pid = pid.lower()
                item.code = f"{pid}{month}"
                item.month = int(month)
                item.pid = pid
                item.hold = row["open_interest"]
                item.close = row["close"]
                item.volume = row["volume"]
                if dtStr not in self.day_cache.keys():
                    self.day_cache[dtStr] = dict()
                if exchg not in self.day_cache[dtStr].keys():
                    self.day_cache[dtStr][exchg] = dict()
                self.day_cache[dtStr][exchg][item.code] = item
                
        if self.pkl_file != "":
            with open(self.pkl_file,"wb") as f:
                pickle.dump(self.day_cache,f)

    def get_cache(self, exchg:str, curDT:datetime.datetime):
        '''
        获取指定日期的某个交易所合约的快照数据

        @exchg  交易所代码
        @curDT  指定日期
        '''
        dtStr = curDT.strftime('%Y%m%d')

        if dtStr not in self.day_cache:
            return None

        if exchg not in self.day_cache[dtStr]:
            return None
        return self.day_cache[dtStr][exchg]
    
    def get_delivery_day(self,code,work_day_delay=0,month=False):
        code = code.upper()
        try:
            date = datetime.datetime.strptime(self.all_info.loc[code,"maturity_date"],"%Y-%m-%d")
        except:
            date = None
        
        if work_day_delay == 0:
            return date
        if date is not None:
            if month:
                date = date.replace(day=1)
            date = rq.get_previous_trading_date(date,work_day_delay)
        return date

class WtCacheMonSS(WtCacheMon):
    '''
    快照缓存管理器
    通过读取wtpy的datakit当日生成的快照文件，缓存当日行情数据
    一般目录为"数据存储目录/his/snapshots/xxxxxxx.csv"
    '''

    def __init__(self, snapshot_path:str):
        WtCacheMon.__init__(self)
        self.snapshot_path = snapshot_path

    def cache_snapshot(self, curDT:datetime):
        '''
        缓存指定日期的快照数据

        @curDT  指定的日期
        '''
        dtStr = curDT.strftime('%Y%m%d')

        filename = "%s%s.csv" % (self.snapshot_path, dtStr)
        content = readFileContent(filename)
        lines = content.split("\n")

        if dtStr not in self.day_cache:
            self.day_cache[dtStr] = dict()

        cacheItem = self.day_cache[dtStr]
        for idx in range(1, len(lines)):
            line = lines[idx]
            if len(line) == 0:
                break
            items = line.split(",")
            
            exchg = items[1]
            if exchg not in cacheItem:
                cacheItem[exchg] = dict()

            day = DayData()
            day.pid = extractPID(items[2])
            day.code = items[2]
            # 收盘价
            day.close = float(items[6])
            # 成交量
            day.volume = int(items[8])
            # 持仓量
            day.hold = int(items[10])
            day.month = day.code[len(day.pid):]
            if len(day.month) == 3:
                if day.month[0] >= '0' and day.month[0] <= '5':
                    day.month = "2" + day.month
                else:
                    day.month = "1" + day.month
            cacheItem[exchg][day.code] = day

    def get_cache(self, exchg, curDT:datetime):
        '''
        获取指定日期的某个交易所合约的快照数据

        @exchg  交易所代码
        @curDT  指定日期
        '''

        dtStr = curDT.strftime('%Y%m%d')
        if dtStr not in self.day_cache:
            self.cache_snapshot(curDT)

        if dtStr not in self.day_cache:
            return None

        if exchg not in self.day_cache[dtStr]:
            return None
        return self.day_cache[dtStr][exchg]

class WtMailNotifier:
    '''
    邮件通知器
    '''
    def __init__(self, user:str, pwd:str, sender:str=None, host:str="smtp.exmail.qq.com", port=465, isSSL:bool = True):
        self.user = user
        self.pwd = pwd
        self.sender = sender if sender is not None else "WtHotNotifier<%s>" % (user)
        self.receivers = list()

        self.mail_host = host
        self.mail_port = port
        self.mail_ssl = isSSL

    def add_receiver(self, name:str, addr:str):
        '''
        添加收件人

        @name   收件人姓名
        @addr   收件人邮箱地址
        '''
        self.receivers.append({
            "name":name,
            "addr":addr
        })

    def notify(self, hot_changes:dict, sec_changes:dict, nextDT:datetime.datetime, hotFile:str, hotMap:str, secFile:str, secMap:str):
        '''
        通知主力切换事件

        @hot_changes    当日主力切换的规则列表
        @sec_changes    当日次主力切换的规则列表
        @nextDT         生效日期
        @hotFile        主力规则文件
        @hotMap         主力映射文件
        '''
        dtStr = nextDT.strftime('%Y.%m.%d')
    
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.application import MIMEApplication
        from email.header import Header

        sender = self.sender
        receivers = self.receivers

        content = ''
        for exchg in hot_changes:
            for pid in hot_changes[exchg]:
                item = hot_changes[exchg][pid][-1]
                content +=  '品种%s.%s的主力合约已切换,下个交易日(%s)生效, %s -> %s\n' % (exchg, pid, dtStr, item["from"], item["to"])

        content += '\n'
        for exchg in sec_changes:
            for pid in sec_changes[exchg]:
                item = sec_changes[exchg][pid][-1]
                content +=  '品种%s.%s的次主力合约已切换,下个交易日(%s)生效, %s -> %s\n' % (exchg, pid, dtStr, item["from"], item["to"])

        msg_mp = MIMEMultipart()
        msg_mp['From'] = sender  # 发送者          
        
        subject = '主力合约换月邮件<%s>' % (dtStr)
        msg_mp['Subject'] = Header(subject, 'utf-8')

        content = MIMEText(content, 'plain', 'utf-8')
        msg_mp.attach(content)

        xlspart = MIMEApplication(open(hotFile,'rb').read())
        xlspart["Content-Type"] = 'application/octet-stream'
        xlspart.add_header('Content-Disposition','attachment', filename=os.path.basename(hotFile))
        msg_mp.attach(xlspart)

        xlspart = MIMEApplication(open(hotMap,'rb').read())
        xlspart["Content-Type"] = 'application/octet-stream'
        xlspart.add_header('Content-Disposition','attachment', filename=os.path.basename(hotMap))
        msg_mp.attach(xlspart)

        xlspart = MIMEApplication(open(secFile,'rb').read())
        xlspart["Content-Type"] = 'application/octet-stream'
        xlspart.add_header('Content-Disposition','attachment', filename=os.path.basename(secFile))
        msg_mp.attach(xlspart)

        xlspart = MIMEApplication(open(secMap,'rb').read())
        xlspart["Content-Type"] = 'application/octet-stream'
        xlspart.add_header('Content-Disposition','attachment', filename=os.path.basename(secMap))
        msg_mp.attach(xlspart)

        if self.mail_ssl:
            smtpObj = smtplib.SMTP_SSL(self.mail_host, self.mail_port)
        else:
            smtpObj = smtplib.SMTP(self.mail_host, self.mail_port)

        try:
            smtpObj.ehlo()
            smtpObj.login(self.user, self.pwd) 
            logging.info("%s 登录成功 %s:%d", self.user, self.mail_host, self.mail_port)
        except smtplib.SMTPException as ex:
            logging.error("邮箱初始化失败：{}".format(ex))

        for item in receivers:
            to = "%s<%s>" % (item["name"], item["addr"])
            msg_mp['To'] =  Header(to, 'utf-8')    # 接收者
            try:
                smtpObj.sendmail(sender, item["addr"], msg_mp.as_string())
                logging.info("邮件发送失败，收件人: %s", to)
            except smtplib.SMTPException as ex:
                logging.error("邮件发送失败，收件人：{}, {}".format(to, ex))
                