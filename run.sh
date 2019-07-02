#开始跑回测
rqalpha run -f main.py -s 2018-01-01 -e 2018-12-30
# 更新概念板块数据
python3 rightTradeModel/common/concept.py