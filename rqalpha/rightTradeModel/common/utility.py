import numpy as np
# import pdb


class Utility:
    @staticmethod
    def calRatio(data):
        s1 = np.delete(data, 0, axis=0)
        s2 = np.delete(data, -1, axis=0)
        return (s1-s2)/s2

    @staticmethod
    def isContinueRiseStop(prices, max_co_present):
        threshold = 0.095
        continueCeiling = 0
        data = Utility.calRatio(prices)
        for ratio in data[-max_co_present:]:
            if ratio >= threshold:
                continueCeiling += 1
                if continueCeiling >= max_co_present:
                    return True
            else:
                continueCeiling = 0
        return False

    @staticmethod
    def isRiseStopNow(prices):
        threshold = 0.095
        data = Utility.calRatio(prices)
        if data[-1] >= threshold:
            return True
        else:
            return False

    @staticmethod
    def isContinueFallStop(prices, min_co_present):
        threshold = -0.095
        continueFloor = 0
        data = Utility.calRatio(prices)
        for ratio in data:
            if ratio <= threshold:
                continueFloor += 1
                if continueFloor >= min_co_present:
                    return True
            else:
                continueFloor = 0
        return False

    @staticmethod
    def isFallStopNow(prices):
        threshold = -0.095
        data = Utility.calRatio(prices)
        if data[-1] <= threshold:
            return True
        else:
            return False

    @staticmethod
    def isabsoluteDesc(data):
        # 计算趋势，对数据做拟合然后取趋势就好了
        flag = data[0]
        for val in data[1:]:
            if val < flag:
                flag = val
            else:
                return False
        return True

    @staticmethod
    def isabsoluteIncr(data):
        flag = data[0]
        for val in data[1:]:
            if val > flag:
                flag = val
            else:
                return False
        return True

    @staticmethod
    def isDescTrend(prices):
        pass

    @staticmethod
    def isIncrTrend(prices):
        pass

    @staticmethod
    def isSHZstock(stock):
        _, market = stock.split('.')
        if market == 'XSHG':
            return True
        else:
            return False

    @staticmethod
    def isSZCstock(stock):
        _, market = stock.split('.')
        if market == 'XSHE':
            return True
        else:
            return False

    @staticmethod
    def incraceRate(incr, orign):
        return (incr - orign) / orign

    @staticmethod
    def avgCrossCheck(open_price, close_price, avg_price):
        if close_price > avg_price and open_price < avg_price:
            return True
        return False

    @staticmethod
    def avgPositionCheck(close_price, open_price, avg_list, ratio):
        # avg_list = [avg20, avg30, avg_60]
        # ratio between [0,1]
        avg_cur = sum(avg_list) / len(avg_list)
        raise_space = open_price + (close_price - open_price) * ratio
        return avg_cur >= raise_space


if __name__ == '__main__':
    data = [23.7, 23.78, 23.72, 23.96, 23.9, 23.85, 23.81, 23.72, 23.75,
            23.7, 23.72, 23.49, 23.5, 23.53, 23.38, 22.82, 20.54, 18.49,
            16.64, 17.55, 15.8]

    data = Utility.checkContinueFloor(data, 4)
    print(data)
