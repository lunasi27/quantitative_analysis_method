from rightTradeModel.selectionRules import SelBuyButtom
from rightTradeModel.selectionRules import SelChaseRise
from rightTradeModel.selectionRules import SelSeekBoard
from rightTradeModel.common.mongo import SelectionDB
from rqalpha.api.api_base import all_instruments
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

    def getStocks(self):
        # 获取所有开盘的股票
        stock = all_instruments('CS')
        active_stock_df = stock[stock.status=='Active']
        return active_stock_df.order_book_id

    def refining(self, sbb_stocks, scr_stocks, ssb_stocks):
        sbb_stocks = list(set(sbb_stocks) - set(scr_stocks) - set(ssb_stocks))
        scr_stocks = list(set(scr_stocks) - set(ssb_stocks))
        return sbb_stocks, scr_stocks, ssb_stocks
    
    def saveSelection(self, stocks, reason, today):
        for stock in stocks:
            self.seldb.insertSelectData(stock, reason, today)

    def run(self, context):
        stocks = self.getStocks()
        # 搜索符合选股条件的股票
        sbb_stocks = self.sbb.search(stocks)
        scr_stocks = self.scr.search(stocks)
        ssb_stocks = self.ssb.search(stocks)
        # 保证选出的股票中没有交叉
        self.sbb_stocks, self.scr_stocks, self.ssb_stocks = self.refining(sbb_stocks, scr_stocks, ssb_stocks)
        #print('抄底候选(%d)：%s' % (len(self.sbb_stocks), self.sbb_stocks))
        #print('追涨候选(%d)：%s' % (len(self.scr_stocks), self.scr_stocks))
        #print('打板候选(%d)：%s' % (len(self.ssb_stocks), self.ssb_stocks))
        # 将选出的股票写入数据库(选股表)
        self.saveSelection(self.sbb_stocks, '抄底', context.now)
        self.saveSelection(self.scr_stocks, '追涨', context.now)
        self.saveSelection(self.ssb_stocks, '打板', context.now)
        # 检查过期股票的操作，被转移到买入之前，这种选择更合理
        # self.seldb.markExpired(context.now)


