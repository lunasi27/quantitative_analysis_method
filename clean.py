from common.mongo import SelectionDB, TradingDB, PositionDB


if __name__ == '__main__':
    dbs = [SelectionDB(), TradingDB(), PositionDB()]
    for db in dbs:
        db.clean()
    print('All data cleaned ...')
