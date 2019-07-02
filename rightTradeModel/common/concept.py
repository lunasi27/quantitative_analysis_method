# from rightTradeModel.common.mongo import TradeDB
import pymongo
import tushare as ts
import datetime
import re
import pdb

#科普：

#   沪市A股：600， 601， 603 开头
#   深市A股：000 开头
#   中小板： 002 开头
#   创业板： 300 开头


class Concept:
    def __init__(self):
        client = pymongo.MongoClient(host='localhost', port=27017)
        db = client.test
        self.collection = db.concept

    def insertData(self, item):
        stock_id, stock_name, conception = item
        if re.match('600|601|603',stock_id):
            stock_id = '%s.XSHG' % stock_id
        elif re.match('000|002|300',stock_id):
            stock_id = '%s.XSHE' % stock_id
        # 从Tushare这边读取概念板块数据
        #['code', 'name', 'c_name']
        concept_data = {
            'code': stock_id,
            'name': stock_name,
            'c_name': conception,
            'date': datetime.datetime.today()
        }
        self.collection.insert_one(concept_data)

    def writeDataFrame(self, c_df):
        for idx in c_df.index:
            self.insertData(c_df.loc[idx])

    def queryData(self, c_name):
        for item in self.collection.find({'c_name': c_name}):
            print(item)


if __name__ == '__main__':
    cpt_db = Concept()
    #cpt_df = ts.get_concept_classified()
    #cpt_db.writeDataFrame(cpt_df)
    cpt_db.queryData('军工航天')
    #print(result)