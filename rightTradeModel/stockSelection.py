from rightTradeModel.selectionBase import SelBuyButtom
from rightTradeModel.selectionBase import SelChaseRise
from rightTradeModel.selectionBase import SelSeekBoard
from rightTradeModel.common.mongo import SelectionDB
import pdb

class StockSelection:
    def __init__(self):
        self.sbb_stocks = []
        self.scr_stocks = []
        self.ssb_stocks = []
        # filter
        self.sbb = SelBuyButtom()
        self.scr = SelChaseRise()
        self.ssb = SelSeekBoard()
        # Selection DB
        self.seldb = SelectionDB()

    def run(self, stocks, context):
        sbb_stocks = self.sbb.search(stocks)
        scr_stocks = self.scr.search(stocks)
        ssb_stocks = self.ssb.search(stocks)
        # 保证选出的股票中没有交叉
        self.sbb_stocks, self.scr_stocks, self.ssb_stocks = self.refining(sbb_stocks, scr_stocks, ssb_stocks)
        #print('抄底候选(%d)：%s' % (len(self.sbb_stocks), self.sbb_stocks))
        #print('追涨候选(%d)：%s' % (len(self.scr_stocks), self.scr_stocks))
        #print('打板候选(%d)：%s' % (len(self.ssb_stocks), self.ssb_stocks))
        # 将选出的股票直接写入数据库的选股表
        self.write2Db(self.sbb_stocks, '抄底', context.now)
        self.write2Db(self.scr_stocks, '追涨', context.now)
        self.write2Db(self.ssb_stocks, '打板', context.now)
    
    def refining(self, sbb_stocks, scr_stocks, ssb_stocks):
        sbb_stocks = list(set(sbb_stocks) - set(scr_stocks) - set(ssb_stocks))
        scr_stocks = list(set(scr_stocks) - set(ssb_stocks))
        return sbb_stocks, scr_stocks, ssb_stocks
    
    def write2Db(self, stocks, reason, cur_time):
        for stock in stocks:
            self.seldb.insertSelectData(stock, reason, cur_time)

