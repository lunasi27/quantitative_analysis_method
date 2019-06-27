from rqalpha.api.api_base import history_bars
from rightTradeModel.common.mongo import MongoDB

import pdb

# 注意买卖方法实际上调用的是分时方法，所以要注意函数周期的选取。

class TradeRules:
    def __init__(self):
        # 初始化当前日期变量
        self.today = None
        self.db = MongoDB()
        #self.stocks = stocks
        self.sell_stocks = []
        self.buy_stocks = []
        # 买入方法
        self.bbtn = BuyButtom()
        self.bris = BuyRise()
        self.bbod = BuyBoard()
        # 卖出方法
        self.spdb = PeakdrawBack()
        self.stls = StopLoss()

    def sell(self):
        # 成本区检测，处于成本区的持仓不做止盈止损判断
        print('run to checking ...')
        sell_stocks = self.CostZoneCheck()
        # 止盈策略
        sell_peak_draw_back = self.spdb.search(sell_stocks, self.sell_candidate, self.today)
        print('peak_draw_back sell %d' % len(sell_peak_draw_back))
        self.setSellStocksInfo(sell_peak_draw_back, '峰值回撤', '短线')
        # 剔除上一步已经选出的股票
        #sell_stocks = list(set(sell_stocks) - set(sell_peak_draw_back))
        # 止损策略
        sell_stop_loss_stocks = self.stls.search(sell_stocks, self.sell_candidate)
        print('stop_loss sell %d' % len(sell_stop_loss_stocks))
        self.setSellStocksInfo(sell_stop_loss_stocks, '固定幅度止损', '短线')
        # 去除重复的股票
        self.sell_stocks = list(set(sell_peak_draw_back) | set(sell_stop_loss_stocks))
        # 在数据库中标记已卖出的股票
        return self.sell_stocks

    def CostZoneCheck(self):
        # 获取目前处在可卖区的股票
        self.getSellStocksInfo()
        # 卖出规则：成本区检查
        print('cost checking ...')
        # 买入价和现价之间的差值比例小于5%，可视为成本区
        const_zone_threshold = 0.05
        sell_stocks = []
        for stock in self.sell_candidate.keys():
            close = history_bars(stock, 5, '1d', 'close')
            buy_price = self.sell_candidate[stock][1]
            # increase_rate = (now - past) / past
            chg_rate = (close[-1] - buy_price) / buy_price
            if chg_rate > const_zone_threshold or \
               chg_rate < -const_zone_threshold:
                sell_stocks.append(stock)
        #self.stocks_candidate = [s for s in self.stocks_candidate if s not in keep_stocks]
        print('Sell %d' % len(sell_stocks))
        return sell_stocks

    def getSellStocksInfo(self):
        # 从数据库获取候选股票的买入信息
        self.sell_candidate = self.db.searchSellCandidate()
        # sell_candidate = {<stock>:(<buy_date>,<buy_price>), ...}

    def setSellStocksInfo(self, sell_stocks, sell_reason, position_type):
        # 往数据库写入已经卖掉的股票信息
        for stock in sell_stocks:
            sell_price = history_bars(stock, 1, '1d', 'close')[-1]
            self.db.insertSellData(stock, sell_price, sell_reason, position_type, self.today)

    def SetBuyStocksInfo(self, buy_stocks, buy_reason, position_type):
        # 将即将买入股票的信息写入数据库
        for stock in buy_stocks:
            buy_price = history_bars(stock, 1, '1d', 'close')[-1]
            self.db.insertBuyData(stock, buy_price, buy_reason, position_type, 0, '测试阶段', self.today)


    def buy(self, stock_selector):
        # 获取依然还在持仓的股票，已经持仓的股票就不再买入了（补仓情况另行考虑）
        hold_stocks = self.db.searchSellCandidate()
        # 开始进行买入条件判断
        bb_stocks = self.bbtn.search(stock_selector.sbb_stocks)
        self.SetBuyStocksInfo(bb_stocks, '抄底', '短线')
        cr_stocks = self.bris.search(stock_selector.scr_stocks)
        self.SetBuyStocksInfo(cr_stocks, '追涨', '短线')
        sb_stocks = self.bbod.search(stock_selector.ssb_stocks)
        self.SetBuyStocksInfo(sb_stocks, '打板', '短线')
        #co_stocks = list(set(bb_stocks) & set(cr_stocks) & set(sb_stocks))
        buy_stocks = set(bb_stocks) | set(cr_stocks) | set(sb_stocks)
        self.buy_stocks = list(buy_stocks - set(hold_stocks.keys()))
        return self.buy_stocks


class PeakdrawBack:
    # 卖出规则：峰值回撤
    def __init__(self):
        self.retreat_threshold = -0.06
    
    def search(self, stocks, sc_dict, today):
        sell_stocks = []
        for stock in stocks:
            buy_date = sc_dict[stock][0]
            period = (today - buy_date).days + 1
            highs = history_bars(stock, period, '1d', 'high')
            close = history_bars(stock, period, '1d', 'close')
            # increase_rate = (now - past) / past
            retreat_rate = (close[-1] - highs.max()) / highs.max()
            if retreat_rate <= self.retreat_threshold:
                sell_stocks.append(stock)
        return sell_stocks


class StopLoss:
    # 卖出规则：固定止损
    def __init__(self):
        self.retreat_threshold = -0.05
        self.period = 5

    def search(self, stocks, sc_dict):
        sell_stocks = []
        for stock in stocks:
            buy_price = sc_dict[stock][1]
            close = history_bars(stock, self.period, '1d', 'close')
            # increase_rate = (now - past) / past
            retreat_rate = (close[-1] - buy_price) / buy_price
            if retreat_rate <= self.retreat_threshold:
                sell_stocks.append(stock)
        return sell_stocks


class BuyButtom:
    # 买入规则：抄底
    def __init__(self):
        self.period = 5

    def search(self, stocks):
        bam_stocks = self.breakAtMiddle(stocks)
        rat_stocks = self.redAtTail(stocks)
        return list(set(bam_stocks + rat_stocks))
    
    def breakAtMiddle(self, stocks):
        # 盘中突破
        rise_threshold = 0.04
        buy_stocks = []
        for stock in stocks:
            opens = history_bars(stock, self.period, '1d', 'open')
            close = history_bars(stock, self.period, '1d', 'close')
            incr_rate = (close[-1] - close[-2]) / close[-2]
            if incr_rate > rise_threshold:
                # 盘中涨幅超过4%
                buy_stocks.append(stock)
        return buy_stocks

    def redAtTail(self, stocks):
        # 尾盘红盘
        buy_stocks = []
        for stock in stocks:
            close = history_bars(stock, self.period, '1d', 'close')
            # 可以考虑用小时来判断是否是尾盘，比如2:30之后。
            if close[-1] > close[-2]:
                # 尾盘红盘后可考虑买入
                buy_stocks.append(stock)
        return buy_stocks


class BuyRise():
    # 买入规则：追涨
    def __init__(self):
        self.period = 5

    def search(self, stocks):
        bro_stocks = self.bigRiseOpen(stocks)
        bfo_stocks = self.bigFallOpen(stocks)
        sro_stocks = self.smallRiseOpen(stocks)
        return list(set(bro_stocks + bfo_stocks + sro_stocks))
    
    def bigRiseOpen(self, stocks):
        # 大幅高开，直接追
        rise_threshold = 0.07
        buy_stocks = []
        for stock in stocks:
            opens = history_bars(stock, self.period, '1d', 'open')
            close = history_bars(stock, self.period, '1d', 'close')
            # increase_rate = (now - past) / past
            open_rate = (opens[-1] - close[-2]) / close[-2]
            if open_rate > rise_threshold:
                buy_stocks.append(stock)
        return buy_stocks

    def bigFallOpen(self, stocks):
        # 大幅低开，放心追
        rise_threshold = -0.07
        buy_stocks = []
        for stock in stocks:
            opens = history_bars(stock, self.period, '1d', 'open')
            close = history_bars(stock, self.period, '1d', 'close')
            # increase_rate = (now - past) / past
            open_rate = (opens[-1] - close[-2]) / close[-2]
            if open_rate < rise_threshold:
                buy_stocks.append(stock)
        return buy_stocks

    def smallRiseOpen(self, stocks):
        # 小幅高开，看看再追
        rise_threshold = 0.05
        buy_stocks = []
        for stock in stocks:
            opens = history_bars(stock, self.period, '1d', 'open')
            close = history_bars(stock, self.period, '1d', 'close')
            lows = history_bars(stock, self.period, '1d', 'low')
            # increase_rate = (now - past) / past
            open_rate = (opens[-1] - close[-2]) / close[-2]
            if open_rate < rise_threshold and open_rate > 0:
                if lows[-1] <= opens[-1]:
                    # 回补日内缺口
                    buy_stocks.append(stock)
        return buy_stocks


class BuyBoard:
    # 买入规则：打板
    def __init__(self):
        self.period = 5
    
    def search(self, stocks):
        bfo_stocks = self.bigFallOpen(stocks)
        return bfo_stocks
    
    def bigFallOpen(self, stocks):
        # 大幅低开，放心追
        rise_threshold = -0.07
        buy_stocks = []
        for stock in stocks:
            opens = history_bars(stock, self.period, '1d', 'open')
            close = history_bars(stock, self.period, '1d', 'close')
            # increase_rate = (now - past) / past
            open_rate = (opens[-1] - close[-2]) / close[-2]
            if open_rate < rise_threshold:
                buy_stocks.append(stock)
        return buy_stocks 
