from rightTradeModel.tradeRules import CostZone,ContinueBoard,PeakdrawBack,StopLoss
from rightTradeModel.tradeRules import BuyButtom,BuyRise,BuyBoard
from rightTradeModel.common.mongo import SelectionDB,TradingDB,PositionDB
# from rightTradeModel.stockPosition import StockPosition
# RQAlpha交易相关API
from rqalpha.mod.rqalpha_mod_sys_accounts.api.api_stock import order_value,order_target_percent 
from rqalpha.const import ORDER_STATUS
import logging
import pdb



# 买卖方法实际上调用的是分时方法，所以要注意函数周期的选取 ???
class StockTrading:
    def __init__(self):
        self.logger = logging.getLogger('Trade_Logger')
        # 初始化交易数据库连接
        self.sdb = SelectionDB()
        self.tdb = TradingDB()
        self.pdb = PositionDB()
        # 把仓位管理集成在交易规则里：
        # 因为，只有在交易时才考虑仓位因素
        # self.position = StockPosition()
        # 买入方法
        self.bbtn = BuyButtom()
        self.bris = BuyRise()
        self.bbod = BuyBoard()
        # 卖出方法
        self.czck = CostZone()
        self.sctb = ContinueBoard()
        self.spdb = PeakdrawBack()
        self.stls = StopLoss()

    def sell(self, context, bar_dict):
        # 从数据库获取持仓股票的信息
        hold_stocks = self.tdb.getHoldStocks()
        self.logger.info('找到%d只股票，处于持仓状态' % len(hold_stocks))
        # 过滤停盘的股票
        hold_stocks = self.filterSellSuspend(hold_stocks, bar_dict)
        # 先处理打板的股票，如果不能连续涨停即离场
        sell_board = self.sctb.search(hold_stocks)
        # 成本区检测，处于成本区的持仓不做止盈止损判断
        sell_candidate,force_sell,keep_cost_zone = self.czck.search(hold_stocks, context.now)
        # 峰值回撤止盈检测
        sell_peak_draw_back = self.spdb.search(sell_candidate, hold_stocks, context.now)
        # 剔除上一步已经选出的股票
        sell_candidate = list(set(sell_candidate) - set(sell_peak_draw_back))
        # 止损策略
        sell_stop_loss_stocks = self.stls.search(sell_candidate, hold_stocks)
        # 使用Rqalpha的API尝试卖出
        self.try2Sell('打板止盈', sell_board, context)
        self.try2Sell('强制平仓', force_sell, context)
        self.try2Sell('峰值回撤', sell_peak_draw_back, context)
        self.try2Sell('固定止损', sell_stop_loss_stocks, context)
        # 如果仓位指导从高位下降到低位，为了调整仓位而进行的额外操作。
        # 其实这不是一个好主意，也可以限制只卖不买。
        # if self.posiMngt.isPositionExceed(context):
        #     # 仓位超限
        #     self.try2Sell('强制平仓',keep_cost_zone, context)

    def buy(self, context, bar_dict):
        # 从数据库获取选出的股票，（标记过期的选股，并剔除）
        select_stocks = self.sdb.getSelectStocks(context.now)
        # 设置仓位控制信息
        self.setupPositionConstraint(context)
        if not self.bp_sh:
            # 当没有出现买点时，不买股票
            return
        # pdb.set_trace()
        # 过滤停盘的股票
        # pdb.set_trace()
        select_stocks = self.filterBuySuspend(select_stocks, bar_dict)
        # 抄底买入条件判断
        bb_stocks = self.bbtn.search(select_stocks['抄底'] if '抄底' in select_stocks else [])
        # 追涨买入条件判断
        cr_stocks = self.bris.search(select_stocks['追涨'] if '追涨' in select_stocks else [])
        # 打板买入条件判断
        sb_stocks = self.bbod.search(select_stocks['打板'] if '打板' in select_stocks else [])
        # 使用Rqalpha的API尝试买入
        self.try2Buy('抄底', bb_stocks, context)
        self.try2Buy('追涨', cr_stocks, context)
        self.try2Buy('打板', sb_stocks, context)

    def setupPositionConstraint(self, context):
        p_dict = self.pdb.getPosition(context.now)
        if p_dict is None:
            # 第一次运行时，没有计算出仓位信息。
            # 就在这初始化仓位相关变量
            self.position_threshold = 0
            self.bp_sh = False
            self.bp_sz = False
        else:
            self.position_threshold = p_dict['position']
            # 当某个市场有买点的时候, 才买入相应的股票
            self.bp_sh = p_dict['buy_point_sh']
            self.bp_sz = p_dict['buy_point_sz']

    def filterSellSuspend(self, hold_stocks, bar_dict):
        sell_candidate = {}
        for stock in hold_stocks.keys():
            if not bar_dict[stock].suspended:
                sell_candidate[stock] = hold_stocks[stock]
        return sell_candidate

    def filterBuySuspend(self, select_stocks, bar_dict):
        # 过滤正在持仓的股票
        # 过滤当天停盘的股票
        hold_stocks = self.tdb.getHoldStocks()
        for buy_reason in select_stocks.keys():
            stocks = select_stocks[buy_reason]
            buy_candidate =[]
            for stock in stocks:
                if not (bar_dict[stock].suspended or stock in hold_stocks):
                    buy_candidate.append(stock)
            select_stocks[buy_reason] = buy_candidate
        return select_stocks

    def try2Sell(self, sell_reason, stocks, context):
        position_type = '短线'
        sell_count = 0
        for stock in stocks:
            stat = self.sellExec(stock)
            if stat:
                sell_count += 1
                sell_price = stat.avg_price
                # 如果成功卖出，就将其写入交易数据库
                self.tdb.insertSellData(stock, sell_price, sell_reason, position_type, context.now)
                self.logger.debug('%s卖出股票%s, 价格%f' % (sell_reason, stock, sell_price))
        self.logger.info('%s卖出%d支股票' % (sell_reason, sell_count))

    def try2Buy(self, buy_reason, stocks, context):
        position_type = '短线'
        buy_count = 0
        for stock in stocks:
            # 获取当前的买入额度
            buy_quota = self.calculateBuyQuota(context)
            stat = self.buyExec(stock, buy_quota)
            if stat:
                buy_count += 1
                buy_price = stat.avg_price
                # 如果买入成功，就将股票信息写入数据库
                self.sdb.updateSelectStat(stock)
                self.tdb.insertBuyData(stock, buy_price, buy_reason, position_type, 0, '测试阶段', context.now)
                self.logger.debug('%s买入股票%s, 价格%f' % (buy_reason, stock, buy_price))
        self.logger.info('%s买入%d支股票' % (buy_reason, buy_count))

    def sellExec(self, stock):
        # 清仓卖出股票
        stat = order_target_percent(stock, 0)
        if (stat is not None) and (stat.status == ORDER_STATUS.FILLED):
            return stat
        else:
            return False

    def buyExec(self, stock, quota):
        # 按配额买入股票
        stat = order_value(stock, quota)
        if (stat is not None) and (stat.status == ORDER_STATUS.FILLED):
            # 只有买成功了才返回值
            return stat
        else:
            return False

    def calculateBuyQuota(self, context):
        # 可用现金
        cash = context.stock_account.cash
        # 股票市值
        market_value = context.stock_account.market_value
        # 账户总资产
        total_value = context.stock_account.total_value
        # 将账户总资划分为 50 份，一份一份买入
        piece = total_value // 50
        # 计算仓位
        position_rate = market_value / total_value
        # 判断目前仓位是否符合仓位控制条件
        if position_rate < self.position_threshold:
            # 有可用仓位
            return piece if cash > piece else cash
        else:
            return 0
