from rqalpha.api.api_base import history_bars
import numpy as np
import pdb


class PositionManagement:
    def __init__(self):
        self.mt = MarketType()

    def getPositionPeriod(self):
        # 长线/中线/短线
        print('getPositionPeriod')
        pass

    def checkMarketMode(self):
        # 牛市/熊市
        pass

    def riskAnalysis(self, stocks):
        # 高风险/低风险
        self.mt.search(stocks)



class MarketType:
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
            if self.LessThentQ(close_prices, 97):
                uc_97 += 1
            if self.LessThentQ(close_prices, 85):
                uc_85 += 1
            if self.LessThentQ(close_prices, 50):
                uc_50 += 1
            if self.LessThentQ(close_prices, 15):
                uc_15 += 1
            if self.LessThentQ(close_prices, 3):
                uc_3 += 1
        #upper_rate = upper_counter / total
        #lower_rate = lower_counter / total
        print([uc_97, uc_85, uc_50, uc_15, uc_3])
        pdb.set_trace()
        print('Upper rate: %s, Lower_rate: %s' % (upper_rate, lower_rate))
    
    def GreatTanQ(self, data, quantile):
        # print(data[-1], np.percentile(data, quantile))
        if data[-1] >= np.percentile(data, quantile):
            return True
        return False

    def LessThentQ(self, data, quantile):
        if data[-1] < np.percentile(data, quantile):
            return True
        return False


