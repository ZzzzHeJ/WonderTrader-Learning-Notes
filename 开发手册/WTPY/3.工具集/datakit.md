---
sort: 3
---

# datakit

对应demo地址[datakit](https://github.com/ZzzzHeJ/WonderTrader-Learning-Notes/tree/demo/dataFeed)

仿真或实盘中的实时行情，需要通过datakit工具实时接收，datakit将接受到的行情分发给不同的策略，同时并保存到本地作为当日的历史行情，在收盘后会的盘后处理中，将当日数据合并到历史行情中。盘后工作的时间取决于datakit的配置文件statemonitor.yaml

# dtcfg.yaml

datakit工具配置，制定了基础配置文件的所在目录、行情分发设置以及指定其他配置文件

```yaml
basefiles:                                    # 基础配置文件目录
    commodity: ..\common\commodities.json
    contract: ..\common\contracts.json
    holiday: ..\common\holidays.json
    session: ..\common\sessions.json
broadcaster:                                  # 数据广播设置
    active: true
    bport: 3997                               # 端口
    broadcast:                                # 广播设置，策略配置中tdparsers.yaml的配置需要与这个一致，否则无法接收到数据
    -   host: 255.255.255.255
        port: 9001
        type: 2
    multicast_:
    -   host: 224.169.169.169
        port: 9002
        sendport: 8997
        type: 0
    -   host: 224.169.169.169
        port: 9003
        sendport: 8998
        type: 1
    -   host: 224.169.169.169
        port: 9004
        sendport: 8999
        type: 2
parsers: mdparsers.yaml                       # 行情服务设置
statemonitor: statemonitor.yaml               # 状态设置
writer:                                       # 行情记录设置
    module: WtDtStorage     #数据存储模块
    async: true             #同步落地还是异步落地，期货推荐同步，股票推荐异步
    groupsize: 20           #日志分组大小，主要用于控制日志输出，当订阅合约较多时，推荐1000以上，当订阅的合约数较少时，推荐100以内
    path: ../STK_Data       #数据存储的路径
    savelog: false          #是否保存tick到csv
    disabletick: false      #不保存tick数据，默认false
    disablemin1: false      #不保存min1数据，默认false
    disablemin5: false      #不保存min5数据，默认false
    disableday: false       #不保存day数据，默认false
    disabletrans: false     #不保存股票l2逐笔成交数据，默认false
    disableordque: false    #不保存股票l2委托队列数据，默认false
    disableorddtl: false    #不保存股票l2逐笔委托数据，默认false
    disablehis: false       #收盘作业不转存历史数据，默认false
    

```

```tip
如果需要开启多个datakit的话，需要设置不同的bport与path
```

# statemonitor.yaml

datakit的配置文件之一，指定了不同交易时段品种的收盘时间，初始化时间，名称以及盘后工作时间

```yaml
FD0900:
    closetime: 1515     # 收盘时间
    inittime: 850       # 初始化时间
    name: 期白0900      # 名称
    proctime: 1600      # 盘后工作时间
FD0915:
    closetime: 1530
    inittime: 900
    name: 期白0915
    proctime: 1600
```

# mdparsers.yaml

行情服务配置

```yaml
parsers:
-   active: true
    broker: '9999'
    code: ''
    front: tcp://180.168.146.187:10211
    id: parser
    module: ParserCTP
    pass: 你的SIMNOW密码
    user: 你的SIMNOW账号
```

# runDT

运行datakit启动代码，开启数据工具

```python
from wtpy import WtDtEngine

if __name__ == "__main__":
    #创建一个运行环境，并加入策略
    engine = WtDtEngine()
    engine.initialize("dtcfg.yaml", "logcfgdt.yaml")
    
    engine.run()

    kw = input('press any key to exit\n')
```
