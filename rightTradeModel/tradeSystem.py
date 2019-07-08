from rightTradeModel.stockSelection import StockSelection
from rightTradeModel.tradeRules import TradeRules
from rightTradeModel.common.mongo import TradeDB
# 只是为了取得卖出买入价格，这个可以后面考虑一下，要不要放在这里
from rqalpha.api.api_base import history_bars
import logging
import pdb


class TradeSystem:
    def __init__(self):
        self.logger = logging.getLogger('System_Logger')
        self.stockSel = StockSelection()
        self.tradRuls = TradeRules()
        # 初始化数据路连接
        self.db = TradeDB()

    def select(self, stocks, context):
        # 选股
        self.logger.info('===<股市收盘，开始选股>===')
        self.stockSel.run(stocks, context)

    def trade(self, context, bar_dict):
        # 交易
        self.logger.info('当前日期：%s' % context.now)
        self.logger.info('===<股票开市，开始交易>===')
        # 获取并过滤目前可以卖出的股票
        sell_candidate = self.getSellCandidate()
        # 执行条件卖出
        sell_dict = self.tradRuls.sell(sell_candidate, context, bar_dict)
        self.writeSellStocks(sell_dict, context.now)
        # 执行条件买入
        buy_dict = self.tradRuls.buy(self.stockSel, context, bar_dict)
        self.writeBuyStocks(buy_dict, context.now)
        print('持仓股票数：%d' % len(context.stock_account.positions.keys()))
    
    def getSellCandidate(self):
        # 从数据库获取候选股票的买入信息
        sell_candidate = self.db.findOpenTradePairs()
        # sell_candidate = {<stock>:(<buy_date>,<buy_price>), ...}
        self.logger.info('找到%d只股票，处于持仓状态' % len(sell_candidate))
        return sell_candidate

    def writeSellStocks(self, sell_dict, today):
        position_type = '短线'
        # 往数据库写入已经卖掉的股票信息
        for sell_reason in sell_dict.keys():
            for stock in sell_dict[sell_reason]:
                sell_price = history_bars(stock, 1, '1d', 'close')[-1]
                # 仓位卖出条件应该处于这个位置
                self.db.insertSellData(stock, sell_price, sell_reason, position_type, today)
                self.logger.debug('%s卖出股票%s, 价格%f' % (sell_reason, stock, sell_price))
            self.logger.info('%s卖出%d支股票' % (sell_reason, len(sell_dict[sell_reason])))

    def writeBuyStocks(self, buy_dict, today):
        position_type = '短线'
        # 找到所有持仓股票
        hold_stocks = self.db.findOpenTradePairs()
        # 将即将买入股票的信息写入数据库
        for buy_reason in buy_dict.keys():
            for stock in buy_dict[buy_reason]:
                # 股票复权问题该怎么解决？300542这个股票在2019年5月8号除权了，导致股价下跌，其实不是亏损，这个该怎么计算？
                # 我需要去查查资料
                #if stock == '300542.XSHE':
                #    pdb.set_trace()
                if stock in hold_stocks.keys():
                    # 已经持仓的股票不再加仓
                    continue
                buy_price = history_bars(stock, 1, '1d', 'close')[-1]
                # 仓位买入条件应该处于这个位置
                self.db.insertBuyData(stock, buy_price, buy_reason, position_type, 0, '测试阶段', today)
                self.logger.debug('%s买入股票%s, 价格%f' % (buy_reason, stock, buy_price))
            self.logger.info('%s买入%d支股票' % (buy_reason, len(buy_dict[buy_reason])))


if __name__ == '__main__':
    ts = TradeSystem()
    ts.stockSel.run()
    #ts.posiMngt.getPositionPeriod()
    #ts.tradRuls.takeProfit()
