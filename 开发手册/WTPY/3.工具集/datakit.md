---
sort: 3
---

# datakit

对应demo地址[datakit](https://github.com/wondertrader/wtpy/tree/master/demos/datakit_fut)

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
    bport: 3997
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
    async: true
    groupsize: 100
    path: ./FUT_Data
    savelog: true

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
    broker: '4500'
    code: ''
    front: tcp://120.25.73.42:41313
    id: GT_Parser
    module: ParserCTP
    user: youname
    pass: yourpass
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
