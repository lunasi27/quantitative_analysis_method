from rightTradeModel.stockSelection import StockSelection
from rightTradeModel.stockTrading import StockTrading
from rightTradeModel.stockPosition import StockPosition
import logging
# import pdb


class TradeSystem:
    def __init__(self):
        self.logger = logging.getLogger('System_Logger')
        self.stockSel = StockSelection()
        self.stockTrd = StockTrading()
        self.stockPos = StockPosition()

    def select(self, context):
        # 选股
        self.logger.info('===<股市收盘，开始选股>===')
        self.stockSel.run(context)

    def trade(self, context, bar_dict):
        # 交易
        self.logger.info('当前日期：%s' % context.now)
        self.logger.info('===<股票开市，开始交易>===')
        # 卖出条件检查, 执行卖出股票
        self.stockTrd.sell(context, bar_dict)
        # 买入条件检查，执行买入股票
        self.stockTrd.buy(context, bar_dict)
        print('持仓股票数：%d' % len(context.stock_account.positions.keys()))

    def calculatePositon(self, context):
        # 计算当前合适持仓比例
        self.stockPos.checkPosition(context)
        print('盘前计算持仓比例')


if __name__ == '__main__':
    ts = TradeSystem()
    ts.stockSel.run()
    # ts.posiMngt.getPositionPeriod()
    # ts.stockTrd.takeProfit()
