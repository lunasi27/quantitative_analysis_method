#from mongoengine import Document, connect, StringField, IntFiled
from mongoengine import *
from datetime import datetime
import pdb


#connection to DB
connect('test')
#connect('test', host='192.168.1.1', username='root', password='1234')

class TradeData(Document):
    # 股票代码
    stock = StringField(max_legth=30, required=True)
    # 买入价格
    buy_price = FloatField(min_value=0, required=True)
    # 卖出价格
    sell_price = FloatField(min_value=0)
    # 买入原因（抄底，追涨，打板）
    buy_reason = StringField(max_legth=30, required=True)
    # 卖出原因（峰值回撤，固定幅度止损）
    sell_reason = StringField(max_legth=30)
    # 持仓类型（长线，中线，短线）
    position_type = StringField(max_legth=10, required=True)
    # 持仓数量
    position_num = IntField(default=0, required=True)
    # 买入时间
    buy_time = DateTimeField(default=datetime.now()) 
    # 卖出时间
    sell_time = DateTimeField(default=None)
    # 市场趋势（牛市，熊市，震荡市）
    market_type = StringField(max_legth=30, required=True)
    # index
    meta = {
        'indexes': [
            'stock'
        ]
    }


class MongoDB:
    def __init__(self):
        self.handler = TradeData()
    
    def insertBuyData(self, stock, buy_price, buy_reason, position_type, position_num, market_type):
        self.handler.stock = stock
        self.handler.buy_price = buy_price
        self.handler.buy_reason = buy_reason
        self.handler.position_type = position_type
        self.handler.position_num = position_num
        self.handler.market_type = market_type
        self.handler.save()
    
    def insertSellData(self, stock, sell_price, sell_reason, position_type):
        TradeData.objects(stock=stock).update(set__sell_price=sell_price)
        TradeData.objects(stock=stock).update(set__sell_reason=sell_reason)
        TradeData.objects(stock=stock).update(set__position_type=position_type)
        TradeData.objects(stock=stock).update(set__sell_time=datetime.now())
    
    def searchSellData(self):
        pdb.set_trace()
        stocks = TradeData.objects(sell_price=None)
        return stocks



#'buy_time', 'sell_time',
if __name__ == '__main__':
    data_list = [{'stock':'1', 'buy_price': 1, 'sell_price': 2, 'buy_reason': '抄底', 'sell_reason': '峰值回撤', 
                  'position_type': '短线', 'position_num': 100, 'market_type': '震荡市'},
                 {'stock':'2', 'buy_price': 3, 'sell_price': 6, 'buy_reason': '追涨', 'sell_reason': '峰值回撤', 
                  'position_type': '短线', 'position_num': 500, 'market_type': '牛市'}]
    # 效率确实让人捉急
    tt = MongoDB()
    for trade in data_list:
        tt.insertBuyData(trade['stock'], trade['buy_price'], trade['buy_reason'], trade['position_type'], trade['position_num'], trade['market_type'])
        ss = tt.searchSellData()
        tt.insertSellData(trade['stock'], trade['sell_price'], trade['sell_reason'], trade['position_type'])
