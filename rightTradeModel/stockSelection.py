from rightTradeModel.selectionBase import SelBuyButtom
from rightTradeModel.selectionBase import SelChaseRise
from rightTradeModel.selectionBase import SelSeekBoard

class StockSelection:
    def __init__(self):
        self.sbb_stocks = []
        self.scr_stocks = []
        self.ssb_stocks = []
        # filter
        self.sbb = SelBuyButtom()
        self.scr = SelChaseRise()
        self.ssb = SelSeekBoard()

    def run(self, stocks):
        print('Begin searching stocks.')
        self.sbb_stocks = self.sbb.search(stocks)
        self.scr_stocks = self.scr.search(stocks)
        self.ssb_stocks = self.ssb.search(stocks)
        print('抄底候选(%d)：%s' % (len(self.sbb_stocks), self.sbb_stocks))
        print('追涨候选(%d)：%s' % (len(self.scr_stocks), self.scr_stocks))
        print('打板候选(%d)：%s' % (len(self.ssb_stocks), self.ssb_stocks))
