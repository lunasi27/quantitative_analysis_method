import pymongo
from datetime import datetime
import pdb

# class TradeData(Document):
#     # 股票代码
#     stock = StringField(max_legth=30, required=True)
#     # 买入价格
#     buy_price = FloatField(min_value=0, required=True)
#     # 卖出价格
#     sell_price = FloatField(min_value=0)
#     # 买入原因（抄底，追涨，打板）
#     buy_reason = StringField(max_legth=30, required=True)
#     # 卖出原因（峰值回撤，固定幅度止损）
#     sell_reason = StringField(max_legth=30)
#     # 持仓类型（长线，中线，短线）
#     position_type = StringField(max_legth=10, required=True)
#     # 持仓数量
#     position_num = IntField(default=0, required=True)
#     # 买入时间
#     buy_time = DateTimeField(default=datetime.now()) 
#     # 卖出时间
#     sell_time = DateTimeField(default=None)
#     # 市场趋势（牛市，熊市，震荡市）
#     market_type = StringField(max_legth=30, required=True)


class TradeDB:
    def __init__(self):
        client = pymongo.MongoClient(host='localhost', port=27017)
        db = client.test
        self.collection = db.trade
    
    def insertBuyData(self, stock, buy_price, buy_reason, position_type, position_num, market_type, buy_time):
        trade_data = {
            'stock': stock,
            'buy_price': buy_price,
            'buy_reason': buy_reason,
            'position_type': position_type,
            'position_num': position_num,
            'market_type': market_type,
            'buy_time': buy_time
        }
        self.collection.insert_one(trade_data)
    
    def insertSellData(self, stock, sell_price, sell_reason, position_type, sell_time):
        trade_data = {
            'sell_price': sell_price,
            'sell_reason': sell_reason,
            'position_type': position_type,
            'sell_time': sell_time
        }
        query = {'stock': stock, 'sell_price': {'$exists': False}}
        value = {'$set': trade_data}
        self.collection.update_one(query, value)

    def findOpenTradePairs(self):
        results = self.collection.find({'sell_price': {'$exists': False}})
        sell_candidate = {item['stock']: (item['buy_time'], item['buy_price'], item['buy_reason'],
                          item['position_num']) for item in results}
        return sell_candidate


class SelectionDB:
    def __init__(self):
        client = pymongo.MongoClient(host='localhost', port=27017)
        db = client.test
        self.collection = db.select

    def insertSelectData(self, stock, sel_reason, sel_time):
        select_data = {
            'stock': stock,
            # 'sel_price': sel_price,
            'sel_reason': sel_reason,
            'sel_time': sel_time
        }
        self.collection.insert_one(select_data)

    def updateSelectStat(self, stock):
        # 被选中的股票会被标上买入
        query = {'status': {'$exists': False}, 'stock': stock}
        select_data = {
            'status': 'buy-in',
        }
        value = {'$set': select_data}
        self.collection.update_one(query, value)

    def markExpired(self, cur_time):
        # 超过5天的股票自动被标上过期
        cur_time -= datetime.timedelta(days=5)
        query = {'status': {'$exists': False}, 'sel_time': {'$lt': cur_time}}
        select_data = {
            'status': 'expired',
        }
        value = {'$set': select_data}
        self.collection.update_one(query, value)

    def findSelectStock(self, cur_time):
        # 找出目前潜在的可买股票
        self.markExpired(cur_time)
        results = self.collection.find({'status': {'$exists': False}})
        sell_candidate = {item['stock']: item['sel_reason'] for item in results}
        return sell_candidate


if __name__ == '__main__':
    data_list = [{'stock':'1', 'buy_price': 1, 'sell_price': 2, 'buy_reason': '抄底', 'sell_reason': '峰值回撤', 
                  'position_type': '短线', 'position_num': 100, 'market_type': '震荡市'},
                 {'stock':'2', 'buy_price': 3, 'sell_price': 6, 'buy_reason': '追涨', 'sell_reason': '峰值回撤', 
                  'position_type': '短线', 'position_num': 500, 'market_type': '牛市'}]
    # 效率不错
    tt = MongoDB()
    for trade in data_list:
        tt.insertBuyData(trade['stock'], trade['buy_price'], trade['buy_reason'], trade['position_type'], trade['position_num'], trade['market_type'])
        ss = tt.findOpenTradePairs()
        for s in ss:
            print(s)
            pdb.set_trace()
        tt.insertSellData(trade['stock'], trade['sell_price'], trade['sell_reason'], trade['position_type'])
