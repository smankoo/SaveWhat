import boto3
import json
from pricecache import get_price_from_cache, set_price_to_cache


# Lookup table for region names
location = dict()
location["us-east-2"] = "US East (Ohio)"
location["us-east-1"] = "US East (N. Virginia)"
location["us-west-1"] = "US West (N. California)"
location["us-west-2"] = "US West (Oregon)"
location["ap-south-1"] = "Asia Pacific (Mumbai)"
location["ap-northeast-2"] = "Asia Pacific (Seoul)"
location["ap-southeast-1"] = "Asia Pacific (Singapore)"
location["ap-southeast-2"] = "Asia Pacific (Sydney)"
location["ap-northeast-1"] = "Asia Pacific (Tokyo)"
location["ca-central-1"] = "Canada (Central)"
location["cn-north-1"] = "China (Beijing)"
location["cn-northwest-1"] = "China (Ningxia)"
location["eu-central-1"] = "EU (Frankfurt)"
location["eu-west-1"] = "EU (Ireland)"
location["eu-west-2"] = "EU (London)"
location["eu-west-3"] = "EU (Paris)"
location["eu-north-1"] = "EU (Stockholm)"
location["sa-east-1"] = "South America (Sao Paulo)"

# Search product filter
FLT = '[{{"Field": "location", "Value": "{l}", "Type": "TERM_MATCH"}},'\
    '{{"Field": "instanceType", "Value": "{t}", "Type": "TERM_MATCH"}},'\
    '{{"Field": "operatingSystem", "Value": "{o}", "Type": "TERM_MATCH"}},'\
    '{{"Field": "preInstalledSw", "Value": "{sw}", "Type": "TERM_MATCH"}},'\
    '{{"Field": "licenseModel", "Value": "{lm}", "Type": "TERM_MATCH"}},'\
    '{{"Field": "tenancy", "Value": "{tt}", "Type": "TERM_MATCH"}}]'


#'{{"Field": "capacitystatus", "Value": "{c}", "Type": "TERM_MATCH"}},'\

# Assumptions

sw = 'NA' # Assume no preinstalled software (e.g. SQL)
c = 'Used' # 'Used' seems the only valid option for OnDemand instances. The others apply to reserved.
lm = 'No License required' # The other option is BYOL. Assume we don't do BYOL for EC2.
tt = 'shared' # Assume we don't use Dedicated tenancy.


# Get current AWS price for an on-demand instance
def get_hourly_price_od(location, instance_type, operating_system ):

    # Replace placeholders with values
    f = FLT.format(l=location, t=instance_type, o=operating_system, sw=sw, c=c, lm=lm, tt=tt)

    # Run query to get data based upon our filters
    data = client.get_products(ServiceCode='AmazonEC2', Filters = json.loads(f))

    rowcount=len(data['PriceList'])

    # Check to make sure our filters narrowed down to just the one SKU
    
    # Narrow down the returned data to just OnDemand instances
    priceitem=data['PriceList'][0]
    od = json.loads(priceitem)['terms']['OnDemand']
    id1 = list(od)[0]
    id2 = list(od[id1]['priceDimensions'])[0]
    firstprice=od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']
    firstprice=float(firstprice)
    
    
    # DEBUG: Price description for debugging purposes. Useful when multiple prices are returned
    # description=od[id1]['priceDimensions'][id2]['description']
    # print('firstprice=' + firstprice + description)

    if rowcount > 1:
        for priceitem in data['PriceList']:
            od = json.loads(priceitem)['terms']['OnDemand']
            # print(od)
            id1 = list(od)[0]
            id2 = list(od[id1]['priceDimensions'])[0]
            newprice=od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']
            newprice=float(newprice)

            # DEBUG: Price description for debugging purposes. Useful when multiple prices are returned
            # description=od[id1]['priceDimensions'][id2]['description']
            # print('NewPrice=' + str(newprice) + ' ' + description)

            # If the other price isn't 0 and is different from the first price, throw error
            if newprice != firstprice:
                if firstprice == 0:
                    firstprice = newprice
                else:
                    if newprice != 0:
                        print('TOO_MANY_SKUS: More than 1 SKU returned with different prices')
                        return('TOO_MANY_SKUS')

            # print('---------------')

    # DEBUG: 
    #print(json.loads(priceitem))
    #print(firstprice)
    return firstprice 


# Use AWS Pricing API at US-East-1
client = boto3.client('pricing', region_name='us-east-1')

def hourly_to_annual(hourly_price):
    try: 
        return round(float(hourly_price) * 24 * 365,2)
    except ValueError:
        return 'ERROR:'+hourly_price

def get_annual_price_od_live(location, instance_type, operating_system = 'Linux'):
    if operating_system is None:
        operating_system = 'Linux'
    # Get current price for a given instance, region and os
    # print('running function: str(hourly_to_annual(get_hourly_price_od('+location+', '+instance_type+', '+operating_system+'))) ')
    return str(hourly_to_annual(get_hourly_price_od(location=location, instance_type=instance_type, operating_system=operating_system)))

def get_annual_price_od(location, instance_type, operating_system = 'Linux'):
    price = get_price_from_cache(location=location, instance_type=instance_type, operating_system=operating_system, terms='OnDemand')
    if price is None:
        price = get_annual_price_od_live(location, instance_type, operating_system)
        set_price_to_cache(location=location, instance_type=instance_type, operating_system = operating_system, terms='OnDemand', price=price)
    return price

def get_annual_price_reserved_live(location, instance_type, operating_system = 'Linux', purchase_option = 'All Upfront'):
    # print('getting upfront price for: ')
    # print('location' + location )
    # print('instance_type ' + instance_type)
    # print('operating_system ' + operating_system)
    # print('purchase_option ' + purchase_option)

    # Replace placeholders with values
    f = FLT.format(l=location, t=instance_type, o=operating_system, sw=sw, c=c, lm=lm, tt=tt)

    # Run query to get data based upon our filters
    data = client.get_products(ServiceCode='AmazonEC2', Filters = json.loads(f))

    firstprice=''

    for priceitem in list(data['PriceList']):
        #print(json.loads(priceitem)['terms'])
        if 'Reserved' in json.loads(priceitem)['terms']:
            res_skus = json.loads(priceitem)['terms']['Reserved']
            for sku_id in list(res_skus):
                # Debug: Print JSONs of all SKUs
                # print(sku_id+ ':')
                # print(res_skus[sku_id])
                if res_skus[sku_id]['termAttributes']['PurchaseOption'] == purchase_option \
                    and res_skus[sku_id]['termAttributes']['OfferingClass'] == 'standard' \
                    and res_skus[sku_id]['termAttributes']['LeaseContractLength'] == '1yr':
                        
                    for price_dimension in list(res_skus[sku_id]['priceDimensions']):
                        # print(price_dimension)

                        # All upfront is measured in "Quantity", all others are measured in "Hrs"
                        if purchase_option == 'No Upfront':
                            unit = 'Hrs'
                        else:
                            unit = 'Quantity'

                        if res_skus[sku_id]['priceDimensions'][price_dimension]['unit'] == unit:
                            # print(res_skus[sku_id]['priceDimensions'])
                            price=res_skus[sku_id]['priceDimensions'][price_dimension]['pricePerUnit']['USD']
                            # print(price)

                            if firstprice == '':
                                firstprice=price
                            else:
                                if price != firstprice and float(price) != 0:
                                    print('TOO_MANY_SKUS: More than 1 SKU returned with different prices')
                                    return('TOO_MANY_SKUS')
                            
                            # print('------------')
    #print('price='+price)
    if purchase_option == 'No Upfront':
        return str(hourly_to_annual(firstprice))
    else:
        return firstprice


def get_annual_price_reserved(location, instance_type, operating_system = 'Linux', purchase_option = 'All Upfront'):

    price = get_price_from_cache(location=location, instance_type=instance_type, operating_system=operating_system, terms=purchase_option)
    if price is None:
        price = get_annual_price_reserved_live(location=location, instance_type=instance_type, operating_system = operating_system, purchase_option = purchase_option)
        set_price_to_cache(location=location, instance_type=instance_type, operating_system = operating_system, terms=purchase_option, price=price)
    return price

#print(get_annual_price_reserved(location=location['us-east-1'], instance_type='t2.micro', operating_system = 'windows', purchase_option = 'No Upfront'))
