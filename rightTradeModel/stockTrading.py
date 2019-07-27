from rightTradeModel.positionManagement import PositionManagement
from rightTradeModel.tradeRules import CostZone,PeakdrawBack,StopLoss
from rightTradeModel.tradeRules import BuyButtom,BuyRise,BuyBoard
import logging
import pdb



# 买卖方法实际上调用的是分时方法，所以要注意函数周期的选取 ???
class TradeRules:
    def __init__(self):
        self.logger = logging.getLogger('Trade_Logger')
        # 把仓位管理集成在交易规则里：
        # 因为，只有在交易时才考虑仓位因素
        self.posiMngt = PositionManagement()
        # 买入方法
        self.bbtn = BuyButtom()
        self.bris = BuyRise()
        self.bbod = BuyBoard()
        # 卖出方法
        self.czck = CostZone()
        self.spdb = PeakdrawBack()
        self.stls = StopLoss()

    def updatePositionConstraint(self, constraint):
        pass

    def sell(self, sell_candidate, context, bar_dict):
        # pdb.set_trace()
        # 过滤停盘的股票
        self.filterSellSuspended(sell_candidate, bar_dict)
        # 成本区检测，处于成本区的持仓不做止盈止损判断
        sell_stocks,force_close,keep_cost_zone,sell_board = self.czck.search(sell_candidate, context.now)
        # 止盈策略
        sell_peak_draw_back = self.spdb.search(sell_stocks, sell_candidate, context.now)
        # 剔除上一步已经选出的股票
        sell_stocks = list(set(sell_stocks) - set(sell_peak_draw_back))
        # 止损策略
        sell_stop_loss_stocks = self.stls.search(sell_stocks, sell_candidate)
        # 使用Rqalpha的API尝试卖出
        self.try2Sell(sell_peak_draw_back)
        self.try2Sell(sell_stop_loss_stocks)
        self.try2Sell(force_close)
        self.try2Sell(sell_board)
        if self.posiMngt.isPositionExceed(context):
            # 仓位超限
            self.try2Sell(keep_cost_zone)
            force_close.extend(keep_cost_zone)
        # 返回挑选出的将要卖出的股票信息     
        return {'峰值回撤': sell_peak_draw_back, '固定止损': sell_stop_loss_stocks,
                '强制平仓': force_close, '打板止盈': sell_board}

    def buy(self, stock_selector, context, bar_dict):
        # 过滤停盘的股票
        # pdb.set_trace()
        self.filterBuySuspended(stock_selector, bar_dict)
        # 抄底买入条件判断
        bb_stocks = self.bbtn.search(stock_selector.sbb_stocks)
        # 追涨买入条件判断
        cr_stocks = self.bris.search(stock_selector.scr_stocks)
        # 打板买入条件判断
        sb_stocks = self.bbod.search(stock_selector.ssb_stocks)
        # 使用Rqalpha的API尝试买入
        self.try2Buy(bb_stocks, context)
        self.try2Buy(cr_stocks, context)
        self.try2Buy(sb_stocks, context)
        for stock in bb_stocks:
            if stock not in context.stock_account.positions.keys():
                pdb.set_trace()
        for stock in cr_stocks:
            if stock not in context.stock_account.positions.keys():
                pdb.set_trace()
        # 返回买入结果
        return {'抄底': bb_stocks, '追涨': cr_stocks, '打板': sb_stocks}

    def filterSellSuspended(self, sell_candidate, bar_dict):
        del_candidate = []
        for stock in list(sell_candidate.keys()):
            if bar_dict[stock].suspended:
                del_candidate.append(stock)
        for stock in del_candidate:
                sell_candidate.pop(stock)
        # self.tradRuls.sell_candidate = sell_candidate
        #self.tradRuls.bar_dict = bar_dict
        # sell_candidate = {<stock>:(<buy_date>,<buy_price>), ...}
        # self.logger.info('找到%d只股票，处于持仓状态' % len(self.tradRuls.sell_candidate))

    def filterBuySuspended(self, stock_selector, bar_dict):
        # 过滤当天停盘的股票
        buy_list = [stock_selector.sbb_stocks, stock_selector.scr_stocks, stock_selector.ssb_stocks]
        for stocks in buy_list:
            del_candidate =[]
            for stock in stocks:
                if bar_dict[stock].suspended:
                    del_candidate.append(stock)
            for stock in del_candidate:
                stocks.remove(stock)
    
    def try2Buy(self, stocks, context):
        buy_fail = []
        for stock in stocks:
            stat = self.posiMngt.buyExec(stock, context)
            if not stat:
                # 如果没有买成功，就从买入列表中删除，保证数据库数据的一致性
                buy_fail.append(stock)
        for stock in buy_fail:
            stocks.remove(stock)

    def try2Sell(self, stocks):
        sell_fail = []
        for stock in stocks:
            stat = self.posiMngt.sellExec(stock)
            if not stat:
                # 如果没有卖成功，就从卖出列表中删除，保证数据库数据的一致性
                sell_fail.append(stock)
        for stock in sell_fail:
            stocks.remove(stock)