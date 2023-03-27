import boto3
import argparse
from botocore.config import Config

#Initialize argparser
parser = argparse.ArgumentParser(description='EC2 compliance check')
parser.add_argument("--regions", type=str, help="AWS region, e.g. --regions='us-east-1,us-east-2'")
args = parser.parse_args()
regions = [args.regions]


#AWS configuration for retry
config = Config(
    retries = dict(
        max_attempts = 10
    )
)


#appends uncompliant security groups to list
uncompliant_ec2_list = []

for region in regions:
    ec2 = boto3.resource('ec2', config=config, region_name=region)

    sgs = list(ec2.security_groups.all())

    for sg in sgs:
        for rule in sg.ip_permissions:
            # Check if list of IpRanges is not empty, source ip meets conditions
            if len(rule.get('IpRanges')) > 0 and rule.get('IpRanges')[0]['CidrIp'] == '0.0.0.0/0':
                if not rule.get('FromPort'):
                    uncompliant_ec2_list.append(sg)
              

                if rule.get('FromPort') and rule.get('FromPort') < rule.get('FromPort') != 80 and rule.get('FromPort') != 443:
                    uncompliant_ec2_list.append(sg)
    
    ec2 = boto3.client('ec2', config=config, region_name=region)
               
    response = ec2.describe_instances()
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            if instance["SecurityGroups"] not in uncompliant_ec2_list:  
                uncompliant_ec2 = {'Instance_ID': instance["InstanceId"], 'Private_IP': instance["PrivateIpAddress"]}
                uncompliant_ec2_list.append(uncompliant_ec2)
    uncompliant_instance_ids = [instance["Instance_ID"] for instance in uncompliant_ec2_list]
    #uncompliant_ec2_list.extend(uncompliant_region)
    if uncompliant_ec2_list:
        response = ec2.stop_instances(InstanceIds=uncompliant_instance_ids,)
        print(f"The ec2s that were shutdown are: {uncompliant_instance_ids}")
    else:
        print("The ec2s that did not shutdown are " + region)
