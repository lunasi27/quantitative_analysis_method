from rightTradeModel.common.mongo import TradingDB
import pdb

class ReadData(TradingDB):
    def __init__(self):
        super(ReadData, self).__init__()

    def read(self):
        results = self.collection.find({'sell_price': {'$exists': True}})
        # {'sell_time': datetime.datetime(2018, 1, 8, 15, 0), 
        # 'position_num': 0, 
        # 'sell_price': 12.15, 
        # 'sell_reason': '强制平仓', 
        # 'buy_time': datetime.datetime(2018, 1, 3, 15, 0), 
        # 'stock': '000555.XSHE', 
        # '_id': ObjectId('5d18c88d1d41c82ec3ab0993'), 
        # 'position_type': '短线', 
        # 'buy_price': 12.03, 
        # 'buy_reason': '抄底', 
        # 'market_type': '测试阶段'}
        profit = 0
        max_rate = 0
        min_rate = 0
        for item in results:
            rate = (item['sell_price'] - item['buy_price']) / item['buy_price']
            if rate > max_rate:
                # if rate > 0.75:
                #     pdb.set_trace()
                max_rate = rate
                buy_hold = (item['sell_time'] - item['buy_time']).days
            if rate < min_rate:
                # 其实最大跌幅，不是真正的最大跌幅，而是因为股票除权导致的
                #if rate < -0.14:
                #    pdb.set_trace()
                min_rate = rate
                sell_hold = (item['sell_time'] - item['buy_time']).days
            profit += rate
            #pdb.set_trace()
            #print(item)
        print('最大涨幅持仓时间: %d, 最大跌幅持仓时间：%d' % (buy_hold, sell_hold))
        print('最大涨幅: %f, 最大跌幅：%f' % (max_rate, min_rate))
        print('最后收入: %s' % profit)

if __name__ == '__main__':
    rd = ReadData()
    rd.read()
