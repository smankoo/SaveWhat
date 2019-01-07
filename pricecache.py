import json
from datetime import timedelta, datetime

def get_price_from_cache(location, instance_type, operating_system, terms):

    try:
        with open('pricecache.json') as json_file:  
            pricecache = json.load(json_file)
            price=pricecache[location][instance_type][operating_system][terms]['price']
            cached_at=pricecache[location][instance_type][operating_system][terms]['cached_at']
            cached_at=datetime.strptime(cached_at, '%Y-%m-%d %H:%M:%S')
            if cached_at > datetime.now() - timedelta(days=1):
                # print('FRESH price found in cache :'+location +','+ instance_type +','+ operating_system +','+ terms +','+ price)
                return price
            else:
                # print('STALE price found in cache :'+location +','+ instance_type +','+ operating_system +','+ terms +','+ price)
                pass

    except:
        # print('Price not found in cache :'+location +','+ instance_type +','+ operating_system +','+ terms )
        pass


def set_price_to_cache(location, instance_type, operating_system, terms, price):
    # print('Setting price in cache :'+location +','+ instance_type +','+ operating_system +','+ terms +','+ price)

    try:
        with open('pricecache.json') as json_file:  
            pricecache = json.load(json_file)
    except:
        pricecache = {}

    # print('Initial Price Cache')
    # print('--------------------')
    # print(pricecache)
    # print('--------------------')


    if location not in pricecache:
        x=pricecache
        x[location] = {}
        pricecache=x
        # print(pricecache)

    if instance_type not in pricecache[location]:
        x=pricecache[location]
        x[instance_type] = {}
        pricecache[location]=x
        # print(pricecache)

    if operating_system not in pricecache[location][instance_type]:
        x=pricecache[location][instance_type]
        x[operating_system] = {}
        pricecache[location][instance_type]=x
        # print(pricecache)

    if terms not in pricecache[location][instance_type][operating_system]:
        x=pricecache[location][instance_type][operating_system]
        x[terms] = {}
        pricecache[location][instance_type][operating_system]=x
        # print(pricecache)


    cached_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    pricecache[location][instance_type][operating_system][terms]['price'] = price
    pricecache[location][instance_type][operating_system][terms]['cached_at'] = cached_at

    # json_data = json.dumps(pricecache)
    # print(json_data)

    with open('pricecache.json', 'w') as outfile:  
        json.dump(pricecache, outfile)

# get_price_from_cache('ludhiana', 'Large', 'Windows', 'OnDemand')