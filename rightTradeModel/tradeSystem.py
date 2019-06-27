from rightTradeModel.stockSelection import StockSelection
from rightTradeModel.positionManagement import PositionManagement
from rightTradeModel.tradeRules import TradeRules


class TradeSystem:
    def __init__(self):
        self.stockSel = StockSelection()
        self.posiMngt = PositionManagement()
        self.tradRuls = TradeRules()
    
    def trade(self, today):
        self.tradRuls.today = today
        self.tradRuls.sell()
        self.tradRuls.buy(self.stockSel)







if __name__ == '__main__':
    ts = TradeSystem()
    ts.stockSel.run()
    #ts.posiMngt.getPositionPeriod()
    #ts.tradRuls.takeProfit()
