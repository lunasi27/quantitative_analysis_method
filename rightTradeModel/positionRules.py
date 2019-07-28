
from rqalpha.api.api_base import history_bars
import talib
import numpy as np
import pdb


class MarketRisk:
    # 这个方法是用来检测股市的极端情况的，比如超跌/过热
    # 一般情况下，这个检查不会触发信号。但是如果触发信号，那么就是极端的逃顶或者抄底的机会。
    def __init__(self):
        self.period = 750

    def search(self, stocks):
        uc_97 = 0
        uc_85 = 0
        uc_50 = 0
        uc_15 = 0
        uc_3 = 0
        total = len(stocks)
        for stock in stocks:
            close_prices = history_bars(stock, self.period, '1d', 'close')
            if len(close_prices) < 90:
                # print('股票：%s, 交易日：%d' % (stock,len(close_prices)))
                total -= 1
                continue
            if self.LessThantQ(close_prices, 97):
                uc_97 += 1
            if self.LessThantQ(close_prices, 85):
                uc_85 += 1
            if self.LessThantQ(close_prices, 50):
                uc_50 += 1
            if self.LessThantQ(close_prices, 15):
                uc_15 += 1
            if self.LessThantQ(close_prices, 3):
                uc_3 += 1
        #upper_rate = upper_counter / total
        #lower_rate = lower_counter / total
        # 如果 uc_50/total 大于 0.5, 说明两市超过50%的股票价格处于低位，熊市特征。
        # 如果 uc_3/total 大于 0.5, 说明两市超过50%的股票价格处于极低水平，股市超跌。
        if uc_3/total > 0.5:
            return 1
        return 0
        #print('[%.2f, %.2f, %.2f, %.2f, %.2f]' % (uc_97/total, uc_85/total, uc_50/total, uc_15/total, uc_3/total))
        # pdb.set_trace()
        #print('Upper rate: %s, Lower_rate: %s' % (upper_rate, lower_rate))
    
    def GreatThanQ(self, data, quantile):
        # print(data[-1], np.percentile(data, quantile))
        if data[-1] >= np.percentile(data, quantile):
            return True
        return False

    def LessThantQ(self, data, quantile):
        if data[-1] < np.percentile(data, quantile):
            return True
        return False

class MarketTrend:
    def __init__(self):
        # 这个类主要是做大盘的量化分析，分析大盘的多空趋势
        self.period = 250
        # 有一个主意，对于追涨和抄底的类的股票，选择处于多头的市场会增大成功率，因此可以可以考虑对选出的股票针对不同的市场板块做筛选。
        pass
    
    def calTrend(self, market_index):
        ema_period = 28
        close_prices = history_bars(market_index, self.period, '1d', 'close')
        close_ema = talib.EMA(close_prices, timeperiod=ema_period)
        today = close_ema[-1]
        yesterday = close_ema[-2]
        return today,yesterday

    def isSHZTrendUp(self):
        # 上证大盘主板趋势
        sh_idx = '000001.XSHG'
        today_val, yesterday_val = self.calTrend(sh_idx)
        if today_val > yesterday_val:
            # print('上证大盘处于：多头趋势')
            return True
        else:
            # today_val <= yesterday_val
            # print('上证大盘处于：空头趋势')
            return False
    
    def isSZCTrendUp(self):
        # 深成指趋势
        sz_idx = '399001.XSHE'
        today_val, yesterday_val = self.calTrend(sz_idx)
        if today_val > yesterday_val:
            # print('深成指处于：多头趋势')
            return True
        else:
            # today_val <= yesterday_val
            # print('深成指处于：空头趋势')
            return False
        pass

    def isSZXTrendUp(self):
        # 中小板趋势
        cy_idx = '399005.XSHE'
        today_val, yesterday_val = self.calTrend(cy_idx)
        if today_val > yesterday_val:
            # print('中小板指处于：多头趋势')
            return True
        else:
            # today_val <= yesterday_val
            # print('中小板指处于：空头趋势')
            return False
        pass

    def isSCYTrendUp(self):
        # 创业板趋势
        cy_idx = '399006.XSHE'
        today_val, yesterday_val = self.calTrend(cy_idx)
        if today_val > yesterday_val:
            # print('创业板指处于：多头趋势')
            return True
        else:
            # today_val <= yesterday_val
            # print('创业板指处于：空头趋势')
            return False
        pass


class MarketBuyPoint:
    def __init__(self):
        # 从大盘出发，分析买点：没有出现买点的时候不能买股
        # 具体思路：
        # 1，上证大盘偏离5日线2%，就可以买上证股
        # 2，深成大盘偏离5日线5%，就可以买深圳股
        self.period = 250
        pass
    
    def buyPointCheck(self):
        sh_idx = '000001.XSHG'
        # 检查上证指数是否存在买点
        sh_stat = self.deviateAvgCheck(sh_idx, -0.02)
        sz_idx = '399001.XSHE'
        # 检查深成指数是否存在买点
        sz_stat = self.deviateAvgCheck(sz_idx, -0.05)
        return sh_stat, sz_stat

    def deviateAvgCheck(self, market, deviate_threshold):
        # 收盘价偏离5日线超过 x%
        deviate_period = 5
        # deviate_threshold = -0.02
        market_close = history_bars(market, self.period, '1d', 'close')
        close = market_close[-1]
        close_ma = talib.MA(market_close, timeperiod=deviate_period)
        avg5 = close_ma[-1]
        deviate_idx = (close - avg5) / avg5
        if deviate_idx <= deviate_threshold:
            # self.logger.debug('%s股价偏离中期均线超过%d'% (stock, deviate_idx*100))
            # 触发买点，你可以买股票了
            return True
        else:
            # 还没有触发买点，你还得继续憋着
            return False
