from rightTradeModel.positionManagement import PositionManagement
from rqalpha.api.api_base import history_bars
from rqalpha.api.api_base import get_trading_dates
from rightTradeModel.common.utility import Utility
import logging
import pdb


# 注意买卖方法实际上调用的是分时方法，所以要注意函数周期的选取。

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



class CostZone:
    def __init__(self):
        # 卖出规则：股票长期处于成本区，强制平仓
        self.const_zone_threshold = 0.05
        self.max_hold_days = 5

    def search(self, sc_dict, today):
        # 优先处理打板股票
        sell_board = self.seekBoardCheck(sc_dict)
        # 检查成本区
        sell_stocks,force_close,keep_cost_zone = self.costZoneCheck(sc_dict, today)
        return sell_stocks,force_close,keep_cost_zone,sell_board
    
    def costZoneCheck(self, sc_dict, today):
        sell_stocks = []
        force_close = []
        keep_cost_zone = []
        for stock in sc_dict.keys():
            close = history_bars(stock, 5, '1d', 'close')
            buy_price = sc_dict[stock][1]
            # increase_rate = (now - past) / past
            chg_rate = (close[-1] - buy_price) / buy_price
            # 如果超过5%的成本区，就可以准备做卖出检查了
            if chg_rate > self.const_zone_threshold or \
               chg_rate < -self.const_zone_threshold:
                sell_stocks.append(stock)
            else:
            # 如果持股天数超过5天，就强制卖出
                buy_date = sc_dict[stock][0]
                #hold_days = (today - buy_date).days + 1
                hold_days = len(get_trading_dates(buy_date, today))
                if hold_days >= self.max_hold_days:
                    force_close.append(stock)
                else:
            # 剩下的就是还留在成本区的股票
                    keep_cost_zone.append(stock)
        return sell_stocks,force_close,keep_cost_zone

    def seekBoardCheck(self, sc_dict):
        # 涨停卖出规则：买入条件为打板时，只要不能连续涨停就卖出
        sell_stocks = []
        for stock in sc_dict.keys():
            close = history_bars(stock, 5, '1d', 'close')
            buy_reason = sc_dict[stock][2]
            if buy_reason == '打板' \
               and not Utility.isRiseStopNow(close):
                sell_stocks.append(stock)
        # 从可卖股票中删除打板股票，以免对后续处理造成影响
        for stock in sell_stocks:
            sc_dict.pop(stock)
        return sell_stocks

class PeakdrawBack:
    # 卖出规则：峰值回撤
    def __init__(self):
        self.retreat_threshold = -0.06
    
    def search(self, stocks, sc_dict, today):
        sell_stocks = []
        for stock in stocks:
            buy_date = sc_dict[stock][0]
            period = (today - buy_date).days + 1
            highs = history_bars(stock, period, '1d', 'high')
            close = history_bars(stock, period, '1d', 'close')
            # increase_rate = (now - past) / past
            retreat_rate = (close[-1] - highs.max()) / highs.max()
            if retreat_rate <= self.retreat_threshold:
                sell_stocks.append(stock)
        return sell_stocks


class StopLoss:
    # 卖出规则：固定止损
    def __init__(self):
        self.retreat_threshold = -0.05
        self.period = 5

    def search(self, stocks, sc_dict):
        sell_stocks = []
        for stock in stocks:
            buy_price = sc_dict[stock][1]
            close = history_bars(stock, self.period, '1d', 'close')
            # increase_rate = (now - past) / past
            retreat_rate = (close[-1] - buy_price) / buy_price
            if retreat_rate <= self.retreat_threshold:
                sell_stocks.append(stock)
        return sell_stocks


class BuyButtom:
    # 买入规则：抄底
    def __init__(self):
        self.period = 5

    def search(self, stocks):
        bam_stocks = self.breakAtMiddle(stocks)
        rat_stocks = self.redAtTail(stocks)
        return list(set(bam_stocks + rat_stocks))
    
    def breakAtMiddle(self, stocks):
        # 盘中突破
        rise_threshold = 0.04
        buy_stocks = []
        for stock in stocks:
            opens = history_bars(stock, self.period, '1d', 'open')
            close = history_bars(stock, self.period, '1d', 'close')
            # 涨幅 = (now - past) / past 
            incr_rate = (close[-1] - close[-2]) / close[-2]
            if incr_rate > rise_threshold:
                # 盘中涨幅超过4%
                buy_stocks.append(stock)
        return buy_stocks

    def redAtTail(self, stocks):
        # 尾盘红盘
        buy_stocks = []
        for stock in stocks:
            close = history_bars(stock, self.period, '1d', 'close')
            # 可以考虑用小时来判断是否是尾盘，比如2:30之后。
            if close[-1] > close[-2]:
                # 尾盘红盘后可考虑买入
                buy_stocks.append(stock)
        return buy_stocks


class BuyRise():
    # 买入规则：追涨
    def __init__(self):
        self.period = 5

    def search(self, stocks):
        #bro_stocks = self.bigRiseOpen(stocks)
        bfo_stocks = self.bigFallOpen(stocks)
        sro_stocks = self.smallRiseOpen(stocks)
        #return list(set(bro_stocks + bfo_stocks + sro_stocks))
        return list(set(bfo_stocks + sro_stocks))
    
    def bigRiseOpen(self, stocks):
        # 大幅高开，直接追
        rise_threshold = 0.07
        rise_stop = 0.095
        buy_stocks = []
        for stock in stocks:
            opens = history_bars(stock, self.period, '1d', 'open')
            close = history_bars(stock, self.period, '1d', 'close')
            # increase_rate = (now - past) / past
            open_rate = (opens[-1] - close[-2]) / close[-2]
            if open_rate > rise_stop:
                # 开盘涨停的就不用分析了，跟不上的
                continue
            if open_rate > rise_threshold:
                buy_stocks.append(stock)
        return buy_stocks

    def bigFallOpen(self, stocks):
        # 大幅低开，放心追
        rise_threshold = -0.07
        buy_stocks = []
        for stock in stocks:
            opens = history_bars(stock, self.period, '1d', 'open')
            close = history_bars(stock, self.period, '1d', 'close')
            # increase_rate = (now - past) / past
            open_rate = (opens[-1] - close[-2]) / close[-2]
            if open_rate < rise_threshold:
                buy_stocks.append(stock)
        return buy_stocks

    def smallRiseOpen(self, stocks):
        # 小幅高开，看看再追
        rise_threshold = 0.05
        buy_stocks = []
        for stock in stocks:
            opens = history_bars(stock, self.period, '1d', 'open')
            close = history_bars(stock, self.period, '1d', 'close')
            lows = history_bars(stock, self.period, '1d', 'low')
            # increase_rate = (now - past) / past
            open_rate = (opens[-1] - close[-2]) / close[-2]
            if open_rate < rise_threshold and open_rate > 0:
                if lows[-1] <= close[-2] \
                   and close[-1] > opens[-1]:
                    # 回补日内缺口
                    # 且必须收红
                    buy_stocks.append(stock)
        return buy_stocks


class BuyBoard:
    # 买入规则：打板
    def __init__(self):
        self.period = 5
    
    def search(self, stocks):
        bfo_stocks = self.bigFallOpen(stocks)
        return bfo_stocks
    
    def bigFallOpen(self, stocks):
        # 大幅低开，放心追
        rise_threshold = -0.07
        buy_stocks = []
        for stock in stocks:
            opens = history_bars(stock, self.period, '1d', 'open')
            close = history_bars(stock, self.period, '1d', 'close')
            # increase_rate = (now - past) / past
            open_rate = (opens[-1] - close[-2]) / close[-2]
            if open_rate < rise_threshold:
                buy_stocks.append(stock)
        return buy_stocks 
