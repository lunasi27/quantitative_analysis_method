from rqalpha.api.api_base import history_bars
from rightTradeModel.common.utility import Utility
import logging
import pdb


# 注意买卖方法实际上调用的是分时方法，所以要注意函数周期的选取。

class TradeRules:
    def __init__(self):
        self.logger = logging.getLogger('Trade_Logger')
        # 初始化当前日期变量
        self.today = None
        # 初始化卖出候选
        self.sell_candidate = {}
        # 买入方法
        self.bbtn = BuyButtom()
        self.bris = BuyRise()
        self.bbod = BuyBoard()
        # 卖出方法
        self.czck = CostZone()
        self.spdb = PeakdrawBack()
        self.stls = StopLoss()

    def sell(self):
        # 成本区检测，处于成本区的持仓不做止盈止损判断
        sell_stocks,force_close,sell_board = self.czck.search(self.sell_candidate, self.today)
        # 止盈策略
        sell_peak_draw_back = self.spdb.search(sell_stocks, self.sell_candidate, self.today)
        # 剔除上一步已经选出的股票
        sell_stocks = list(set(sell_stocks) - set(sell_peak_draw_back))
        # 止损策略
        sell_stop_loss_stocks = self.stls.search(sell_stocks, self.sell_candidate)
        # 返回挑选出的将要卖出的股票信息
        return {'峰值回撤': sell_peak_draw_back, '固定止损': sell_stop_loss_stocks, '强制平仓': force_close, '打板止盈': sell_board}

    def buy(self, stock_selector):
        # 抄底买入条件判断
        bb_stocks = self.bbtn.search(stock_selector.sbb_stocks)
        # 追涨买入条件判断
        cr_stocks = self.bris.search(stock_selector.scr_stocks)
        # 打板买入条件判断
        sb_stocks = self.bbod.search(stock_selector.ssb_stocks)
        return {'抄底': bb_stocks, '追涨': cr_stocks, '打板': sb_stocks}


class CostZone:
    def __init__(self):
        # 卖出规则：股票长期处于成本区，强制平仓
        self.const_zone_threshold = 0.05
        self.max_hold_days = 5

    def search(self, sc_dict, today):
        # 优先处理打板股票
        sell_board = self.seekBoardCheck(sc_dict)
        # 检查成本区
        sell_stocks,force_close = self.costZoneCheck(sc_dict, today)
        return sell_stocks,force_close,sell_board
    
    def costZoneCheck(self, sc_dict, today):
        sell_stocks = []
        force_close = []
        for stock in sc_dict.keys():
            close = history_bars(stock, 5, '1d', 'close')
            buy_price = sc_dict[stock][1]
            # increase_rate = (now - past) / past
            chg_rate = (close[-1] - buy_price) / buy_price
            if chg_rate > self.const_zone_threshold or \
               chg_rate < -self.const_zone_threshold:
                sell_stocks.append(stock)
            else:
                buy_date = sc_dict[stock][0]
                hold_days = (today - buy_date).days + 1
                if hold_days >= self.max_hold_days:
                    force_close.append(stock)
        return sell_stocks,force_close

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
        bro_stocks = self.bigRiseOpen(stocks)
        bfo_stocks = self.bigFallOpen(stocks)
        sro_stocks = self.smallRiseOpen(stocks)
        return list(set(bro_stocks + bfo_stocks + sro_stocks))
    
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
                if lows[-1] <= opens[-1]:
                    # 回补日内缺口
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
