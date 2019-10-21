from rightTradeModel.rules.selectionRules import SelBuyButtom
from rightTradeModel.rules.selectionRules import SelChaseRise
from rightTradeModel.rules.selectionRules import SelSeekBoard
from rightTradeModel.common.mongo import SelectionDB
from rqalpha.api.api_base import all_instruments
import pdb


class StockSelection:
    def __init__(self):
        # filter
        self.sbb = SelBuyButtom()
        self.scr = SelChaseRise()
        self.ssb = SelSeekBoard()
        # Selection DB
        self.seldb = SelectionDB()

    def getStocks(self):
        # 获取所有开盘的股票
        stock = all_instruments('CS')
        active_stock_df = stock[stock.status == 'Active']
        return active_stock_df.order_book_id

    def refining(self, sbb_stocks, scr_stocks, ssb_stocks):
        sbb_stocks = list(set(sbb_stocks) - set(scr_stocks) - set(ssb_stocks))
        scr_stocks = list(set(scr_stocks) - set(ssb_stocks))
        return sbb_stocks, scr_stocks, ssb_stocks

    def saveSelection(self, stocks, select_info, sel_type, today):
        for stock in stocks:
            sel_price, sel_reason = select_info[stock]
            self.seldb.insertSelectData(stock, sel_price, sel_reason, sel_type, today)

    def run(self, context):
        stocks = self.getStocks()
        # 搜索符合选股条件的股票
        sbb_stocks, sbb_select_info = self.sbb.search(stocks)
        scr_stocks, scr_select_info = self.scr.search(stocks)
        ssb_stocks, ssb_select_info = self.ssb.search(stocks)
        # 保证选出的股票中没有交叉
        sbb_stocks, scr_stocks, ssb_stocks = self.refining(sbb_stocks, scr_stocks, ssb_stocks)
        # print('抄底候选(%d)：%s' % (len(self.sbb_stocks), self.sbb_stocks))
        # print('追涨候选(%d)：%s' % (len(self.scr_stocks), self.scr_stocks))
        # print('打板候选(%d)：%s' % (len(self.ssb_stocks), self.ssb_stocks))
        # 将选出的股票写入数据库(选股表)
        self.saveSelection(sbb_stocks, sbb_select_info, '抄底', context.now)
        self.saveSelection(scr_stocks, scr_select_info, '追涨', context.now)
        self.saveSelection(ssb_stocks, ssb_select_info, '打板', context.now)
        # 检查过期股票的操作，被转移到买入之前，这种选择更合理
        # self.seldb.markExpired(context.now)
