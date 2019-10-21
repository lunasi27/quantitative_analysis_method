from app.services import source
from datetime import datetime, timedelta


class Select:
    def __init__(self):
        self.collection = source.select
        if self.collection.find_one() is None:
            today = datetime.now()
        else:
            today = self.collection.find_one(sort=[('sel_time', -1)])['sel_time']
        # today = datetime.strptime('2018-05-02', '%Y-%m-%d')
        self.today = today.replace(hour=15, minute=30, second=0, microsecond=0)

    def getBuyLow(self):
        query = {'sel_time': self.today, 'sel_type': '抄底'}
        data_set = self.collection.find(query)
        return data_set

    def getBuyHigh(self):
        query = {'sel_time': self.today, 'sel_type': '追涨'}
        data_set = self.collection.find(query)
        return data_set

    def getBuyStop(self):
        query = {'sel_time': self.today, 'sel_type': '打板'}
        data_set = self.collection.find(query)
        return data_set

    def getSelectPool(self):
        # 获取还在观察期的股票, 暂定5日内
        begin_time = self.today - timedelta(days=7)
        end_time = self.today
        # 取区间时间段的股票
        query = {'$and': [{'sel_time': {'$gt': begin_time}}, {'sel_time': {'$lt': end_time}}]}
        data_set = self.collection.find(query).sort('sel_time', -1)
        return data_set
