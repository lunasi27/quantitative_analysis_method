from app.services import source
# from datetime import datetime, timedelta


class Select:
    def __init__(self):
        self.collection = source.select
        today = self.collection.find_one(sort=[('sel_time', -1)])['sel_time']
        # today = datetime.strptime('2018-05-02', '%Y-%m-%d')
        self.today = today.replace(hour=15, minute=30, second=0, microsecond=0)

    def getBuyLow(self):
        query = {'sel_time': self.today, 'sel_reason': '抄底'}
        data_set = self.collection.find(query)
        return data_set

    def getBuyHigh(self):
        query = {'sel_time': self.today, 'sel_reason': '追涨'}
        data_set = self.collection.find(query)
        return data_set

    def getBuyStop(self):
        query = {'sel_time': self.today, 'sel_reason': '打板'}
        data_set = self.collection.find(query)
        return data_set

    def getSelectPool(self):
        # 获取还在观察期的股票
        query = {'status': {'$exists': False}, 'sel_time': {'$lt': self.today}}
        data_set = self.collection.find(query)
        return data_set
