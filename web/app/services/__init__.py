# from mongoengine import 
from pymongo import MongoClient
from app.config import config

# 初始化web数据库
# db = MongoAlchemy()
# 初始化数据源数据库
cfg = config.get('default')
client = MongoClient(cfg.SOURCE_SERVER, cfg.SOURCE_PORT)
source = client[cfg.SOURCE_DB]
