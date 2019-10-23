import pymongo
from datetime import timedelta, datetime, time
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


class TradingDB:
    def __init__(self):
        client = pymongo.MongoClient(host='localhost', port=27017)
        db = client.test
        self.collection = db.trade

    def clean(self):
        self.collection.drop()

    def insertBuyData(self, stock, buy_price, buy_reason, position_type, position_num, market_type, sel_time, buy_time):
        # 插入买入的股票信息
        trade_data = {
            'stock': stock,
            'buy_price': buy_price,
            'buy_reason': buy_reason,
            'position_type': position_type,
            'position_num': position_num,
            'market_type': market_type,
            'sel_time': sel_time,
            'buy_time': buy_time
        }
        self.collection.insert_one(trade_data)

    def insertSellData(self, stock, sell_price, sell_reason, position_type, sell_time):
        # 更新卖出股票的信息
        trade_data = {
            'sell_price': sell_price,
            'sell_reason': sell_reason,
            'position_type': position_type,
            'sell_time': sell_time
        }
        query = {'stock': stock, 'sell_price': {'$exists': False}}
        value = {'$set': trade_data}
        self.collection.update_one(query, value)

    def getHoldStocks(self):
        # 查找可卖出的股票
        results = self.collection.find({'sell_price': {'$exists': False}})
        sell_candidate = {item['stock']: (item['buy_time'], item['buy_price'], item['buy_reason'],
                          item['position_num'], item['sel_time']) for item in results}
        return sell_candidate


# class SelectionData(Document):
#     # 股票代码
#     stock = StringField(max_legth=30, required=True)
#     # 仓位上限：0%~40%, 41%~70%, 71%~100%
#     sel_reason = StringField(max_legth=30)
#     # 是否已经被买入
#     status = BoolField()
#     # 选出时的收盘价格
#     sel_price = FloatField()
#     # 选出时间
#     sel_time = DateTimeField()

class SelectionDB:
    def __init__(self):
        client = pymongo.MongoClient(host='localhost', port=27017)
        db = client.test
        self.collection = db.select

    def clean(self):
        self.collection.drop()

    def insertSelectData(self, stock, stock_name, sel_price, sel_reason, sel_type, sel_time):
        # 在写入数据库前，先判断当前的股票是否在5天前被选出（考虑周末所以使用7天）
        # query = {'status': {'$exists': False}, 'stock': stock}
        query = {'stock': stock, 'sel_time': {'$gt': sel_time - timedelta(days=7)}}
        result = self.collection.find_one(query)
        if result is None:
            # 如果是新股票，则直接写入数据
            # 如果是之前被选出的股票，则跳过不处理（如果一直不被买入，则会标为过期）
            select_data = {
                'stock': stock,
                'name': stock_name,
                'sel_price': sel_price,
                'sel_reason': sel_reason,
                'sel_type': sel_type,
                'sel_time': sel_time
            }
            self.collection.insert_one(select_data)

    def getSelectDate(self, stock):
        # 先找出最大时间戳的记录，往后倒推7天即可
        query = {'status': {'$exists': False}, 'stock': stock}
        result = self.collection.find_one(query)
        if result is None:
            return None
        else:
            return result['sel_time']

    def updateSelectStat(self, stock):
        # 被选中交易的股票会被标上买入
        query = {'status': {'$exists': False}, 'stock': stock}
        select_data = {
            'status': 'buy-in',
        }
        value = {'$set': select_data}
        self.collection.update_one(query, value)

    # sell_candidate = {item['stock']: item['sel_reason'] for item in results}
    # 输出格式为 sell_candidate = {'抄底': ['000546.XSHE', '300223.XSHE', ...], '追涨':['601116.XSHG', '300308.XSHE', ...], ...}
    def _format_output(self, results):
        sell_candidate = {}
        for item in results:
            reason = item['sel_reason']
            stock = item['stock']
            if reason in sell_candidate:
                sell_candidate[reason].append(stock)
            else:
                sell_candidate[reason] = [stock]
        return sell_candidate

    def getSelectStocks(self, cur_time):
        self._markExpired(cur_time)
        cur_time = cur_time.replace(hour=0, minute=0, second=0, microsecond=0)
        if cur_time.isoweekday() == 1:
            # 如果时间是周一的话，需要回溯3天到上周五，因为股票是收盘后选出来的。
            cur_time -= timedelta(days=3)
        else:
            # 如果是周中的话，之需要回溯一天
            cur_time -= timedelta(days=1)
        # 这里区分之前选出但未过期的股票和当天选出的股票，是因为这两种类型的股票有不同的处理规则。
        # 之前选出但未过期的股票
        results = self.collection.find({'status': {'$exists': False}, 'sel_time': {'$lt': cur_time}})
        previous_select_sotcks = self._format_output(results)
        # 当天选出的股票
        results = self.collection.find({'status': {'$exists': False}, 'sel_time': {'$gt': cur_time}})
        today_select_stocks = self._format_output(results)
        # 输出两组数据，一组是今天之前选出的并且没有被标记为过期的股票， 另一组是今天选出的股票
        return previous_select_sotcks, today_select_stocks

    def _markExpired(self, cur_time):
        if cur_time.isoweekday() == 1:
            # 如果当天是星期1，多加2天
            cur_time -= timedelta(days=2)
        # 超过5天的股票自动被标上过期
        cur_time -= timedelta(days=5)
        query = {'status': {'$exists': False}, 'sel_time': {'$lt': cur_time}}
        select_data = {
            'status': 'expired',
        }
        value = {'$set': select_data}
        # 一次更新所有曾经选出的过期股票
        self.collection.update_many(query, value)

    def getSelectInfo(self, stock, sel_reason):
        query = {'status': {'$exists': False}, 'stock': stock, 'sel_reason': sel_reason}
        result = self.collection.find_one(query)
        if result is None:
            return None
        else:
            return result['sel_info']

# class PosotionData(Document):
#     # 市场类型： 牛市/熊市
#     market_type = StringField(max_legth=30, required=True)
#     # 仓位上限：0%~40%, 41%~70%, 71%~100%
#     position = FloatField(min_value=30, required=True)
#     # 沪市买点是否出现
#     buy_point_sh = BoolField()
#     # 深圳买点是否出现
#     buy_point_sz = BoolField()
#     # 分析日期
#     pos_time = DateTimeField()


class PositionDB:
    def __init__(self):
        client = pymongo.MongoClient(host='localhost', port=27017)
        db = client.test
        self.collection = db.position

    def clean(self):
        self.collection.drop()

    def insertPosition(self, m_type, position, buy_point, p_time):
        # 插入盘前分析出的持仓策略
        position_data = {
            'market_type': m_type,
            'position': position,
            'buy_point_sh': buy_point[0],
            'buy_point_sz': buy_point[1],
            'pos_time': p_time
        }
        self.collection.insert_one(position_data)

    def getPosition(self, p_time):
        # 这里的时间需要注意一下，因为是开盘前计算仓位，所以存入时间是0，取出时需要注意。
        # datetime.combine(p_time.date(), time(0))
        query = {'pos_time': datetime.combine(p_time.date(), time(0))}
        result = self.collection.find_one(query)
        # result = {'market_type': m_type, 'position': position,
        #           'buy_point_sh': buy_point[0], 'buy_point_sz': buy_point[1],
        #           'pos_time': p_time}
        return result


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
