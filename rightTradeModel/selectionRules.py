from rqalpha.api.api_base import history_bars
from rqalpha.api.api_base import get_next_trading_date
from rqalpha.mod.rqalpha_mod_sys_accounts.api.api_stock import is_st_stock
from rqalpha.api.api_base import instruments 
from rightTradeModel.common.utility import Utility
import numpy as np
import logging
import talib

import pdb

class SelectionRuleBase:
    def __init__(self):
        self.logger = logging.getLogger('Selection_Logger')
        self.selected_stocks = []
    
    def search(self, stocks):
        # 在基类中直接过滤掉ST股票
        self.stocks = self.filterST(stocks)
    
    def filterST(self, stocks):
        # ST股票不在分析的范围内
        selected_stocks = []
        for stock in stocks:
            if not is_st_stock(stock):
                selected_stocks.append(stock)
        return selected_stocks

    def periodCheck(self, stocks):
        # 股票上市小于一个月的，不分析
        one_month =20
        selected_stocks = []
        for stock in stocks:
            # 获取上市天数
            on_board_days = instruments(stock).days_from_listed()
            if on_board_days > one_month:
                selected_stocks.append(stock)
        self.logger.info('过滤新股后，剩余股票%s个' % len(selected_stocks))
        return selected_stocks


class SelBuyButtom(SelectionRuleBase):
    # 抄底选股算法
    def __init__(self):
        super(SelBuyButtom, self).__init__()
        self.load_period = 250
        self.rsi_period = 14

    def search(self, stocks):
        super(SelBuyButtom, self).search(stocks)
        # 基本抄底规则
        self.logger.info('<开始筛选符合抄底条件的股票>')
        selected_stocks = self.periodCheck(self.stocks)
        selected_stocks = self.deviateAvgCheck(selected_stocks)
        selected_stocks = self.rsiCheck(selected_stocks)
        selected_stocks = self.fallStopCheck(selected_stocks)
        selected_stocks = self.volShrinkCheck(selected_stocks)
        # 进阶抄底规则
        if len(selected_stocks) > 30:
            self.logger.info('选出抄底股票超过30个，启动优化条件')
            selected_stocks = self.rsiCheckAdv(selected_stocks)
            selected_stocks = self.deviateAvgCheckAdv(selected_stocks)
            selected_stocks = self.bollCheckAdv(selected_stocks)
        self.selected_stocks = selected_stocks
        self.logger.info('符合抄底条件股票%s个' % len(self.selected_stocks))
        return self.selected_stocks

    def deviateAvgCheck(self, stocks):
        # 收盘价偏离20日线超过15%
        deviate_period = 20
        deviate_threshold = -0.15
        selected_stocks = []
        for stock in stocks:
            stock_close = history_bars(stock, deviate_period, '1d', 'close')
            close = stock_close[-1]
            close_ma = talib.MA(stock_close, timeperiod=deviate_period)
            avg20 = close_ma[-1]
            #avg20 = sum(stock_close) / deviate_period
            deviate_idx = (close - avg20) / avg20
            if deviate_idx < deviate_threshold:
                selected_stocks.append(stock)
                self.logger.debug('%s股价偏离中期均线超过%d'% (stock, deviate_idx*100))
        return selected_stocks

    def deviateAvgCheckAdv(self, stocks):
        # 收盘价偏离30日线超过20%
        deviate_period = 30
        deviate_threshold = -0.2
        selected_stocks = []
        for stock in stocks:
            stock_close = history_bars(stock, deviate_period, '1d', 'close')
            close = stock_close[-1]
            close_ma = talib.MA(stock_close, timeperiod=deviate_period)
            avg30 = close_ma[-1]
            deviate_idx = (close - avg30) / avg30
            if deviate_idx < deviate_threshold:
                selected_stocks.append(stock)
                self.logger.debug('%s股价偏离中期均线超过%d'% (stock, deviate_idx*100))
        return selected_stocks

    def rsiCheck(self, stocks):
        # RSI指标低于30
        rsi_threshold = 30
        selected_stocks = []
        for stock in stocks:
            close_prices = history_bars(stock, self.load_period, '1d', 'close')
            rsi_data = talib.RSI(close_prices, timeperiod=self.rsi_period)[-1]
            if rsi_data < rsi_threshold:
                selected_stocks.append(stock)
                self.logger.debug('%s股票RSI值低于下限30，当前RSI=%d' % (stock, rsi_data))
        return selected_stocks

    def rsiCheckAdv(self, stocks):
        # RSI指标低于20
        rsi_threshold = 20
        selected_stocks = []
        for stock in stocks:
            close_prices = history_bars(stock, self.load_period, '1d', 'close')
            rsi_data = talib.RSI(close_prices, timeperiod=self.rsi_period)[-1]
            if rsi_data < rsi_threshold:
                selected_stocks.append(stock)
                self.logger.debug('%s股票RSI值低于下限20，当前RSI=%d' % (stock, rsi_data))
        return selected_stocks

    def fallStopCheck(self, stocks):
        # 一月内不能出现连续跌停，且选出当日不能跌停
        check_period = 20
        selected_stocks = []
        for stock in stocks:
            close_prices = history_bars(stock, check_period+1, '1d', 'close')
            if not (Utility.isContinueFallStop(close_prices, min_co_present=2)
                    or 
                    Utility.isFallStopNow(close_prices)):
                selected_stocks.append(stock)
            else:
                self.logger.debug('%s股票一月内存在连续跌停，剔除' % stock)
        return selected_stocks
    
    def volShrinkCheck(self, stocks):
        check_period = 3
        selected_stocks = []
        for stock in stocks:
            close_prices = history_bars(stock, check_period+1, '1d', 'volume')
            if Utility.isabsoluteDesc(close_prices[:-1]):
                selected_stocks.append(stock)
                self.logger.debug('%s股票选出日前连续3天缩量下跌' % stock)
        return selected_stocks

    def bollCheckAdv(self, stocks):
        check_period = 100
        selected_stocks = []
        # 收盘价跌破下轨
        for stock in stocks:
            close_prices = history_bars(stock, check_period, '1d', 'close')
            upper,middle,lower = talib.BBANDS(close_prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            if close_prices[-1] < lower[-1]:
                selected_stocks.append(stock)
                self.logger.debug('%s收盘跌破Boll线下轨' % stock)
        return selected_stocks


class SelChaseRise(SelectionRuleBase):
    def __init__(self):
        super(SelChaseRise, self).__init__()
        self.rsi_period = 14
        self.load_period = 250

    def search(self, stocks):
        super(SelChaseRise, self).search(stocks)
        # Basic condiction
        self.logger.info('<开始筛选符合追涨条件的股票>')
        selected_stocks = self.periodCheck(self.stocks)
        selected_stocks = self.riseStopCheck(selected_stocks)
        selected_stocks = self.riseRateCheck(selected_stocks)
        selected_stocks = self.breakStrength(selected_stocks)
        selected_stocks = self.rsiCheck(selected_stocks)
        # Advance condiction
        selected_stocks = self.breakAvgsAdv(selected_stocks)
        self.selected_stocks = self.avg120TrendUpAdv(selected_stocks)
        self.logger.info('符合追涨条件股票%d个' % len(self.selected_stocks))
        return self.selected_stocks

    def periodCheck(self, stocks):
        # 股票上市小于一年，且大于8个月的，不分析
        # 股票上市小于一个月的，不分析
        one_year = 250
        eight_month = 167
        one_month =20
        selected_stocks = []
        for stock in stocks:
            # 获取上市天数
            on_board_days = instruments(stock).days_from_listed()
            if on_board_days < one_year:
                if on_board_days < eight_month:
                    if on_board_days > one_month:
                        selected_stocks.append(stock)
            else:
                selected_stocks.append(stock)
        self.logger.debug('过滤掉上市小于一个月或上市大于8个月且小于一年的股票，剩余%d只股票' % len(selected_stocks))
        return selected_stocks
    
    def riseStopCheck(self, stocks):
        # 选出日涨停，且不是连续涨停
        check_period = 10
        selected_stocks = []
        for stock in stocks:
            high_prices = history_bars(stock, check_period+1, '1d', 'high')
            close_prices = history_bars(stock, check_period+1, '1d', 'close')
            # 要求收盘价等于最高价，但要求收盘价高于9.95%
            if Utility.isRiseStopNow(close_prices) \
               and close_prices[-1] == high_prices[-1] \
               and not Utility.isContinueRiseStop(close_prices, max_co_present=2):
                    selected_stocks.append(stock)
                    self.logger.debug('选出当日涨停，且不连续涨停的股票%s' % stock)
        return selected_stocks
        
    def riseRateCheck(self, stocks):
        # 过去10个交易日内，涨幅小于25%
        check_period = 10
        selected_stocks = []
        for stock in stocks:
            close_prices = history_bars(stock, check_period, '1d', 'close')
            rise_rate = (close_prices[-1] - close_prices[0]) / close_prices[0]
            if rise_rate < 0.25:
                selected_stocks.append(stock)
                self.logger.debug('选出过去10个交易日内涨幅小于25%%的股票，当前涨幅%d' % (rise_rate*100))
        return selected_stocks

    def breakStrength(self, stocks):
        # 收盘价创3个交易日新高， 且选出日未出现跳空缺口
        check_period = 3
        selected_stocks = []
        for stock in stocks:
            close_prices = history_bars(stock, check_period, '1d', 'close')
            open_prices = history_bars(stock, check_period, '1d', 'open')
            high_prices = history_bars(stock, check_period, '1d', 'high')
            low_prices = history_bars(stock, check_period, '1d', 'low')
            if close_prices.max() == close_prices[-1]:
                if open_prices[-1] <= high_prices[-2] and open_prices[-1] >= low_prices[-2]:
                    selected_stocks.append(stock)
                    self.logger.debug('选出收盘价创新高且未出现跳空缺口的股票%s' % stock)
        return selected_stocks

    def rsiCheck(self, stocks):
        # 涨停前10个交易日内，RSI指标曾处于50以下
        check_period = 10
        selected_stocks = []
        for stock in stocks:
            close_prices = history_bars(stock, self.load_period, '1d', 'close')
            rsi_data = talib.RSI(close_prices, timeperiod=self.rsi_period)[-check_period:]
            if rsi_data.min() < 50:
                selected_stocks.append(stock)
                self.logger.debug('涨停前10个交易日内，RSI指标小于50的股票%s，目前RSI=%d' % (stock, rsi_data[-1]))
        return selected_stocks

    def breakAvgsAdv(self, stocks):
        # 突破中期均线
        selected_stocks = []
        for stock in stocks:
            close_prices = history_bars(stock, self.load_period, '1d', 'close')
            avg20 = talib.MA(close_prices, timeperiod=20,matype=0)
            avg30 = talib.MA(close_prices, timeperiod=30,matype=0)
            avg60 = talib.MA(close_prices, timeperiod=60,matype=0)
            # 选出三条中期均线中离昨天收盘价最近的数据（且中期均线必须小于收盘价）。
            if (close_prices[-1] > avg60[-1] and close_prices[-2] < avg60[-2]) \
                or (close_prices[-1] > avg30[-1] and close_prices[-2] < avg30[-2]) \
                or (close_prices[-1] > avg20[-1] and close_prices[-2] > avg20[-2]):
                selected_stocks.append(stock)
                self.logger.debug('选出突破中期均线的股票%s' % stock)
        return selected_stocks

    def avg120TrendUpAdv(self, stocks):
        # 250日均线，趋势向上
        selected_stocks = []
        for stock in stocks:
            close_prices = history_bars(stock, self.load_period+3, '1d', 'close')
            avg250 = talib.MA(close_prices, timeperiod=250,matype=0)
            # 选出日前3天120日均线趋势向上
            if avg250[-1] > avg250[-2] and avg250[-2] > avg250[-3]:
                selected_stocks.append(stock)
                self.logger.debug('选出120日均线趋势向上的股票%s' % stock)
        return selected_stocks


class SelSeekBoard(SelectionRuleBase):
    def __init__(self):
        super(SelSeekBoard, self).__init__()

    def search(self, stocks):
        super(SelSeekBoard, self).search(stocks)
        # Basic condiction
        self.logger.info('<开始筛选符合打板条件的股票>')
        selected_stocks = self.periodCheck(self.stocks)
        selected_stocks = self.riseStopCheck(selected_stocks)
        self.selected_stocks = self.tunoverRateCheck(selected_stocks)
        self.logger.info('符合打板条件股票%d个' % len(self.selected_stocks))
        return self.selected_stocks

    def riseStopCheck(self, stocks):
        # 连续3个涨停板，三个涨停必须满足： 1，连续； 2，只有3个，不能多。
        check_period = 10
        selected_stocks = []
        for stock in stocks:
            close_prices = history_bars(stock, check_period+1, '1d', 'close')
            if Utility.isContinueRiseStop(close_prices, max_co_present=3) \
                and not Utility.isContinueRiseStop(close_prices, max_co_present=4):
                    selected_stocks.append(stock)
                    self.logger.debug('选出三连板的股票%s' % (stock))
        return selected_stocks

    def tunoverRateCheck(self, stocks):
        # 换手率数据取不到，因此采用成交量数据代替
        # 换手率=当日成交额/流通股本
        check_period = 3
        selected_stocks = []
        for stock in stocks:
            vols = history_bars(stock, check_period, '1d', 'volume')
            if Utility.isabsoluteIncr(vols):
                selected_stocks.append(stock)
                self.logger.debug('选出成交量逐渐放大的股票%s' % (stock))
        return selected_stocks
