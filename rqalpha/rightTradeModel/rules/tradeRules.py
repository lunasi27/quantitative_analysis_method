from rqalpha.api.api_base import history_bars
from rqalpha.api.api_base import get_trading_dates
from rightTradeModel.common.utility import Utility
from rightTradeModel.common.mongo import SelectionDB
import talib
import pdb


class CostZone:
    def __init__(self):
        # 卖出规则：股票长期处于成本区，强制平仓
        self.const_zone_threshold = 0.05
        self.max_hold_days = 5

    def search(self, sc_dict, today):
        # 检查成本区
        sell_stocks, force_close = self.costZoneCheck(sc_dict, today)
        return sell_stocks, force_close

    def costZoneCheck(self, sc_dict, today):
        sell_stocks = []
        force_close = []
        for stock in sc_dict.keys():
            buy_price = sc_dict[stock][1]
            buy_reason = sc_dict[stock][2]
            close = history_bars(stock, 5, '1d', 'close')
            # increase_rate = (now - past) / past
            chg_rate = (close[-1] - buy_price) / buy_price
            # 如果超过5%的成本区，就可以准备做卖出检查了
            if chg_rate > self.const_zone_threshold or \
               chg_rate < -self.const_zone_threshold:
                sell_stocks.append(stock)
            else:
                # 只有 抄底 才需要检查成本区, 追涨的股票直接加入卖出检查列表
                if not buy_reason == u'抄底':
                    continue
                # 如果持股天数超过5天, 且还在成本区，就强制卖出
                buy_date = sc_dict[stock][0]
                # hold_days = (today - buy_date).days + 1
                hold_days = len(get_trading_dates(buy_date, today))
                if hold_days >= self.max_hold_days:
                    force_close.append(stock)
        return sell_stocks, force_close


class ContinueBoard:
    def __init__(self):
        # 卖出规则：对于追涨的股票，如果不能持续涨停，则在开板日尾盘卖出
        self.period = 5

    def search(self, sc_dict):
        # 处理打板股票
        sell_board = self.seekBoardCheck(sc_dict)
        return sell_board

    def seekBoardCheck(self, sc_dict):
        # 涨停卖出规则：买入条件为打板时，只要不能连续涨停就卖出
        sell_stocks = []
        for stock in sc_dict.keys():
            close = history_bars(stock, self.period, '1d', 'close')
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
        self.retreat_threshold = -0.15

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
                # pdb.set_trace()
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
            # opens = history_bars(stock, self.period, '1d', 'open')
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
        # bro_stocks = self.bigRiseOpen(stocks)
        bfo_stocks = self.bigFallOpen(stocks)
        sro_stocks = self.smallRiseOpen(stocks)
        # return list(set(bro_stocks + bfo_stocks + sro_stocks))
        return list(set(bfo_stocks + sro_stocks))

    def bigRiseOpen(self, stocks):
        # 这条规则应该优化成，涨停开盘，如果开板就追一把。
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


class PendingBuyRise:
    # 延迟追涨规则：有些股票在选出后，并不合符买入条件，所以可以等几天，等它回踩5/10日线时，再考虑买入
    def __init__(self):
        self.period = 20
        self.sdb = SelectionDB()

    def search(self, stocks):
        select_stocks = self.stepBack(stocks)
        # rtm_stocks = self.riseTooMuch(sb_stocks)
        select_stocks = self.aboveBoolMiddelLine(select_stocks)
        select_stocks = self.aboveBreakAvgLine(select_stocks)
        return select_stocks

    def stepBack(self, stocks):
        # 回踩5/10日线企稳，意思就是前一天回踩5日线，然后今天依然在5日线之上
        buy_stocks = []
        for stock in stocks:
            lows = history_bars(stock, self.period, '1d', 'low')
            close = history_bars(stock, self.period, '1d', 'close')
            avg5 = talib.MA(close, timeperiod=5, matype=0)
            avg10 = talib.MA(close, timeperiod=10, matype=0)
            if lows[-2] < avg5[-2] and close[-2] > avg5[-2] and close[-1] > avg5[-1]:
                # 前一天回踩5日线，今天依然收盘在5日线之上
                buy_stocks.append(stock)
            elif lows[-2] < avg10[-2] and close[-2] > avg10[-2] and close[-1] > avg10[-1]:
                # 前一天回踩10日线，今天依然收盘在10日线之上
                buy_stocks.append(stock)
        return buy_stocks

    def aboveBoolMiddelLine(self, stocks):
        # 高于布林线中轨
        # 且必须是红盘才考虑买股票
        buy_stocks = []
        for stock in stocks:
            close = history_bars(stock, self.period, '1d', 'close')
            opens = history_bars(stock, self.period, '1d', 'open')
            upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            if close[-1] >= middle[-1] and close[-1] > opens[-1]:
                buy_stocks.append(stock)
        return buy_stocks

    def aboveBreakAvgLine(self, stocks):
        # 必须高于之前选出时，突破的那条均线
        buy_stocks = []
        for stock in stocks:
            # 找到选出当天的信息
            _, break_through = self.sdb.getSelectInfo(stock, '追涨')
            close = history_bars(stock, break_through, '1d', 'close')
            avg = talib.MA(close, timeperiod=break_through, matype=0)
            if close[-1] > avg[-1]:
                buy_stocks.append(stock)
        return buy_stocks

    def riseTooMuch(self, stocks):
        buy_stocks = []
        for stock in stocks:
            # 找到涨停当天的价格
            select_price, break_through = self.sdb.getSelectInfo(stock, '追涨')
            # 只取五天内的收盘最高价
            close = history_bars(stock, 5, '1d', 'close')
            rise_rate = (max(close) - select_price) / select_price
            if rise_rate <= 0.05:
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
