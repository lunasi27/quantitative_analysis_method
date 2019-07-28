from rightTradeModel.positionRules import MarketRisk,MarketTrend,MarketBuyPoint
from common.mongo import PositionDB


class StockPosition:
    # 确定是否要在当前条件见瞎猫股票
    # 确定没吃股票买多少金额的股票
    def __init__(self):
        self.mrisk = MarketRisk()
        self.mtrend = MarketTrend()
        self.mbuypt = MarketBuyPoint()
        # 仓位
        self.position = 0
        # 仓位数据库
        self.pdb = PositionDB()
    
    def checkPosition(self, context):
        # 牛市：    70~100%
        # 熊市：    0~40%
        # 牛皮市:   40~70%
        if self.mtrend.isSHZTrendUp() and self.mtrend.isSZCTrendUp():
            # 主板和创业板都趋势向上， 牛市
            market_type = '牛市'
            base_position = 1
        elif (not self.mtrend.isSHZTrendUp()) and (not self.mtrend.isSZCTrendUp()):
            # 主板和创业板都趋势向下，熊市
            market_type = '熊市'
            base_position = 0.4
        else:
            # 创业板和主板只有一个趋势向上，牛皮市
            market_type = '牛皮市'
            base_position = 0.5
        # print('当前基础仓位：%2f' % base_position)
        # 保存沪深买点判断
        buy_point = self.mbuypt.buyPointCheck()
        # 将当天的盘前仓位分析信息写入数据库
        self.pdb.insertPosition(market_type, base_position, buy_point, context.now)
    
    def getConfig(self):
        # 返回当前市场行情下的操作策略
        pass
    
    def saveStrategy(self):
        # 保存当前的投资策略，以备后期检查
        pass
    
    def getPositionPeriod(self):
        # 长线/中线/短线
        print('getPositionPeriod')
        pass

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



# 可以写一个方法用来判断大盘分时底背离
# 可以写一个方法用来判断大盘偏离5日线达到2%，创业板5%