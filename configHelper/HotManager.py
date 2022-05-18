import json
import pandas as pd
import datetime as dt

class HotManager(object):
    def __init__(self,json_path):
        self.json_path = json_path
        with open(json_path,"r") as f:
            d = json.load(f)
        row = []
        for exchg,item in d.items():
            for com, infos in item.items():
                for info in infos:
                    row.append(
                        {
                            "exchg" : exchg,
                            "com" : com,
                            "date" : info["date"],
                            "from": info["from"],
                            "newclose" : info["newclose"],
                            "oldclose" : info["oldclose"],
                            "to" : info["to"],
                        }
                    )

        self.df = pd.DataFrame(row)
        self.df["date"] = self.df["date"].astype("str").apply(lambda datetime: dt.datetime.strptime(datetime,"%Y%m%d"))
    
    def get_month_code(self,query_date,query_exchg,query_com):
        codes = self.df[(self.df["exchg"]==query_exchg) & (self.df["com"]==query_com) & (self.df["date"] <= query_date)]["to"].values
        code = ""
        if len(codes) > 0:
            code = codes[-1]
            
        return code

if __name__ == "__main__":
    json_path = "//WIN-52AMQLH0TIA/WonderTrader/common/hots.json"
    query_date = dt.datetime.now()
    query_exchg = "CFFEX"
    query_com = "IC"
    
    hot = HotManager(json_path)
    code = hot.get_month_code(query_date,query_exchg,query_com)