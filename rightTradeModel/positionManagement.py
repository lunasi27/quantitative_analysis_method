from rqalpha.mod.rqalpha_mod_sys_accounts.api.api_stock import order_target_percent
from rqalpha.mod.rqalpha_mod_sys_accounts.api.api_stock import order_value
from rqalpha.api.api_base import history_bars
import talib
import numpy as np
import pdb
from rqalpha.const import ORDER_STATUS


class PositionManagement:
    def __init__(self):
        self.mrisk = MarketRisk()
        self.mtrend = MarketTrend()

    def getPositionPeriod(self):
        # 长线/中线/短线
        print('getPositionPeriod')
        pass

    def checkMarketMode(self):
        # 仓位控制
        # 牛市：    70~100%
        # 熊市：    0~40%
        # 牛皮市:   40~70%
        if self.mtrend.isSHZTrendUp() and self.mtrend.isSZCTrendUp():
            print('牛市, 70%~100%仓位')
            return 1
        elif not self.mtrend.isSHZTrendUp() and not self.mtrend.isSZCTrendUp():
            print('熊市, 0%~40%仓位')
            return 0.4
        else:
            print('牛皮市, 40%~70%仓位')
            return 0.7

    def riskAnalysis(self, stocks):
        # 高风险/低风险
        # return self.mrisk.search(stocks)
        self.mtrend.isSHZTrendUp()
        self.mtrend.isSZCTrendUp()
        self.mtrend.isSCYTrendUp()

    def asdasd(self):
        pass
        # 投资偏好，创业板/主板/中小板
        # 投资偏好，题材板块，稀土/5G/...


# class Position:
#     # 仓位控制
    # def __init__(self):
    #     pass

    def sellExec(self, stock):
        # 正常情况下，清仓卖出股票
        stat = order_target_percent(stock, 0)
        if stat.status == ORDER_STATUS.FILLED:
            return stat
        else:
            return False
    
    def isPositionExceed(self, context):
        # 获取仓位信息
        market_value = context.stock_account.market_value
        total_value = context.stock_account.total_value
        # cash = context.stock_account.cash
        position_rate = market_value / total_value
        if position_rate >= self.checkMarketMode():
            # 仓位超限，需要额外减仓
            # 第一步，清空成本区中的股票
            # 第二步，止盈收益最低的股票(这个需要测试)
            return True 
            
        else:
            return False

    def buyExec(self, stock, context):
        # 获取仓位信息
        market_value = context.stock_account.market_value
        total_value = context.stock_account.total_value
        cash = context.stock_account.cash
        position_rate = market_value / total_value
        # 检查部目前仓位是否符合仓位控制条件
        if position_rate < self.checkMarketMode():
            # 有可用仓位, 可用资金均分买入股票
            piece = total_value // 50
            if cash >= piece:
                # 计划将资金分为50份，一份一份买入
                stat = order_value(stock, piece)
                print('买入操作: %s' % stat)
                if stat.status == ORDER_STATUS.FILLED:
                    # 只有买成功了才返回值
                    return stat
                else:
                    return False
                # return order_value(stock, piece)
            else:
                return False
        else:
            # 无可用仓位， 不买
            return False

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
