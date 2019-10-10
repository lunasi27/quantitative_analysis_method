import pymongo
import pdb

if __name__ == '__main__':
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client.test
    collection = db.select
    #query = {"stock" : "0024833.XSHE"}
    #query = {'status': {'$exists': False}, 'stock': '002483.XSHE'}
    #result = collection.find_one(query)
    results = collection.find({'status': {'$exists': False}})
    sell_candidate = {}
    for item in results:
        sel_reason = item['sel_reason']
        stock = item['stock']
        if sel_reason in sell_candidate:
            sell_candidate[sel_reason].append(stock)
        else:
            sell_candidate[sel_reason] = [stock]
    print(sell_candidate)
    pdb.set_trace()
    print(result)
