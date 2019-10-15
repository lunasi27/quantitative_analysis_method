from rightTradeModel.rules.positionRules import MarketRisk, MarketTrend, MarketBuyPoint
from rightTradeModel.common.mongo import PositionDB
# import pdb


class StockPosition:
    # 确定是否要在当前条件见瞎猫股票
    # 确定没次股票买多少金额的股票
    def __init__(self):
        self.mrisk = MarketRisk()
        self.mtrend = MarketTrend()
        self.mbuypt = MarketBuyPoint()
        # 仓位
        self.position = 0
        # 仓位数据库
        self.pdb = PositionDB()

    def checkPosition(self, context):
        # 确定上证和深成的大盘趋势
        sh_stat = self.mtrend.isSHZTrendUp()
        sz_stat = self.mtrend.isSZCTrendUp()
        # 牛市：    70~100%
        # 熊市：    0~40%
        # 牛皮市:   40~70%
        if sh_stat and sz_stat:
            # 主板和创业板都趋势向上， 牛市
            market_type = '牛市'
            position_limit = 1
            # 在牛市中，要剔除掉超买的点，规避风险
            buy_point = self.mbuypt.overBuyCheck()
        elif (not sh_stat) and (not sz_stat):
            # 主板和创业板都趋势向下，熊市
            market_type = '熊市'
            position_limit = 0.4
            # 在熊市中，要找到超卖的点，寻找机会
            buy_point = self.mbuypt.overSellCheck()
        else:
            # 创业板和主板只有一个趋势向上，牛皮市
            market_type = '牛皮市'
            position_limit = 0.7
            # 为了安全起见，在牛皮市中，只参与超卖机会
            buy_point = self.mbuypt.overSellCheck()
        # print('当前基础仓位：%2f' % position_limit)
        # 将当天的盘前仓位分析信息写入数据库
        self.pdb.insertPosition(market_type, position_limit, buy_point, context.now)

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
# 可以写一个方法用来判断大盘偏离5日线达到2%，创业板5%， 大盘向上偏离说明超买，大盘向下偏离说明超卖了。
# 开盘前统计昨天的涨跌停数据
