from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
# from data import Articles
from getprice import get_annual_price_od, location, get_annual_price_reserved

import boto3


app = Flask(__name__)


class InstanceInfo:
    def __init__(self, instance, region=None):
        self.instance = instance
        self.region = region

class AwsInfo:
    def __init__(self, region=None, access_key=None, secret_access_key=None):
        self.region=region
        self.access_key=access_key
        self.secret_access_key=secret_access_key

class AwsRegion:
    def __init__(self, region_code=None, location_name=None):
        self.region_code=region_code
        self.location_name=location_name

# Used this function for sorting regions alphabetically
def getRegionCode(awsregion):
    return awsregion.region_code

# Home
# EC2 Instances
@app.route('/')
@app.route('/ec2_instances', methods=['GET','POST'])
def ec2_instances():
    awsinfo = AwsInfo()

    all_aws_regions=[]


    for l in location:
        aws_region=AwsRegion(region_code=l, location_name=location[l])
        all_aws_regions.append(aws_region)

    print('location' + str(type(location)))
    print('all_aws_regions' + str(type(all_aws_regions)))

    all_aws_regions.sort(key=getRegionCode)

    if request.method == 'POST':
        
        region = request.form['region']
        access_key = request.form['access_key']
        secret_access_key = request.form['secret_access_key']
        
        awsinfo.region=region
        awsinfo.access_key=access_key
        awsinfo.secret_access_key=secret_access_key

        session = boto3.session.Session(region_name=region,aws_access_key_id = access_key,  aws_secret_access_key = secret_access_key)
        region = session.region_name

        ec2 = boto3.resource('ec2', region_name=region,aws_access_key_id = access_key,  aws_secret_access_key = secret_access_key)

        instances = ec2.instances.all()
        # print('number of instances returned: '+len(ec2.instances))

        instanceinfolist = []

        for instance in instances:
            instanceinfo = InstanceInfo(instance)
            instanceinfo.region = region

            # print(location[instanceinfo.region])
            # print(instance.instance_type)
            # print(instance.platform)

            operating_system = instance.platform

            if operating_system is None:
                operating_system = 'Linux'

            instanceinfo.annual_price_od = get_annual_price_od(location = location[instanceinfo.region], \
                                                                instance_type = instance.instance_type, \
                                                                operating_system = operating_system)
            instanceinfo.annual_price_all_upfront = get_annual_price_reserved(location = location[instanceinfo.region], \
                                                                            instance_type=instance.instance_type, \
                                                                            operating_system = operating_system, 
                                                                            purchase_option='All Upfront')
            instanceinfo.annual_price_no_upfront = get_annual_price_reserved(location = location[instanceinfo.region], \
                                                                            instance_type=instance.instance_type, \
                                                                            operating_system = operating_system, 
                                                                            purchase_option='No Upfront')
            instanceinfolist.append(instanceinfo)
            

        
        return render_template('ec2_instances.html', instanceinfolist = instanceinfolist, awsinfo=awsinfo, all_aws_regions=all_aws_regions )

    else:
        awsinfo.access_key=''
        awsinfo.secret_access_key=''
        return render_template('ec2_instances.html', awsinfo=awsinfo, all_aws_regions=all_aws_regions )
        
@app.route('/test', methods=['GET','POST'])
def login():
    return render_template('test.html')

if __name__ == '__main__':
    app.secret_key = 'secret999'
    app.run(host= '0.0.0.0', debug=True)
 