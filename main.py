from rightTradeModel.tradeSystem import TradeSystem
import pdb


# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    #初始化右侧选股交易系统
    context.ts = TradeSystem()

def before_trading(context):
    # 更新当天交易的股票
    stock = all_instruments('CS')
    stock_df = stock[stock.status=='Active']
    print('Total trade stocks = %s' % len(stock_df))
    context.stocks = stock_df.order_book_id

def after_trading(context):
    ts = context.ts
    stocks = context.stocks
    # 收盘作业:选股
    ts.stockSel.run(stocks)
    # For debug usage
    print(context.now)
    

# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    #pdb.set_trace()
    ts = context.ts
    ts.trade(context.now)
    