#开始跑回测
rqalpha run -f main.py -s 2018-01-01 -e 2018-12-30 -a stock 1000000 -bm 000001.XSHG --plot
# 更新概念板块数据
python3 rightTradeModel/common/concept.py
#
rqalpha update-bundle
