from rightTradeModel.rules.selectionRules import SelBuyButtom
from rightTradeModel.rules.selectionRules import SelChaseRise
from rightTradeModel.rules.selectionRules import SelSeekBoard
from rightTradeModel.rules.selectionRules import SelPoolCheck
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
        self.stock_name_map = {}

    def getStocks(self):
        # 获取所有开盘的股票
        stocks = all_instruments('CS')
        active_stocks_df = stocks[stocks.status == 'Active']
        return active_stocks_df.order_book_id

    def refining(self, sbb_stocks, scr_stocks, ssb_stocks):
        sbb_stocks = list(set(sbb_stocks) - set(scr_stocks) - set(ssb_stocks))
        scr_stocks = list(set(scr_stocks) - set(ssb_stocks))
        return sbb_stocks, scr_stocks, ssb_stocks

    def saveSelection(self, stocks, select_info, sel_type, today):
        # 获取所有股票的ID与名字的对应关系
        stocks_df = all_instruments('CS')
        for stock in stocks:
            # 获取所有股票的ID与名字的对应关系
            loc_row = stocks_df.loc[stocks_df.order_book_id == stock, 'symbol']
            stock_name = loc_row[loc_row.index[0]]
            sel_price, sel_reason = select_info[stock]
            self.seldb.insertSelectData(stock, stock_name, sel_price, sel_reason, sel_type, today)

    def updateSelectionPool(self):
        # 给观察池中的踩破10日线的股票打上标签
        pool_stocks = self.seldb.getPoolSelectDate()
        ignore_stocks = SelPoolCheck(pool_stocks)
        for stock in ignore_stocks:
            print(stock)
            # self.seldb.updateIgnoreStock(stock)

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
        self.updateSelectionPool()
        # 将选出的股票写入数据库(选股表)
        self.saveSelection(sbb_stocks, sbb_select_info, '抄底', context.now)
        self.saveSelection(scr_stocks, scr_select_info, '追涨', context.now)
        self.saveSelection(ssb_stocks, ssb_select_info, '打板', context.now)
        # 检查过期股票的操作，被转移到买入之前，这种选择更合理
        # self.seldb.markExpired(context.now)
