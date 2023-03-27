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
uncompliant_security_groups = []

for region in regions:
    ec2 = boto3.resource('ec2', config=config, region_name=region)

    sgs = list(ec2.security_groups.all())

    for sg in sgs:
        for rule in sg.ip_permissions:
            # Check if list of IpRanges is not empty, source ip meets conditions
            if len(rule.get('IpRanges')) > 0 and rule.get('IpRanges')[0]['CidrIp'] == '0.0.0.0/0':
                if not rule.get('FromPort'):
                    uncompliant_security_groups.append(sg)
              

                if rule.get('FromPort') and rule.get('FromPort') < rule.get('FromPort') != 80 and rule.get('FromPort') != 443:
                    uncompliant_security_groups.append(sg)

           
#compares security groups assigned to instances to the ones in the uncompliant list
uncompliant_ec2_list = []


for region in regions:
    uncompliant_region= [] 
    ec2 = boto3.client('ec2', config=config, region_name=region)

    response = ec2.describe_instances()
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            if instance["SecurityGroups"] not in uncompliant_security_groups:  
                uncompliant_ec2 = {'Instance_ID': instance["InstanceId"], 'Private_IP': instance["PrivateIpAddress"]}
                uncompliant_region.append(uncompliant_ec2)
    uncompliant_instance_ids = [instance["Instance_ID"] for instance in uncompliant_region]
    uncompliant_ec2_list.extend(uncompliant_region)
    if uncompliant_instance_ids:
        response = ec2.stop_instances(InstanceIds=uncompliant_instance_ids,)
        print(f"estas se apagaron: {uncompliant_instance_ids}")
    else:
        print("no se apagaron de " + region)


'''
   
#for table printing
def get_pretty_table(iterable, header):
    max_len = [len(x) for x in header]
    for row in iterable:
        row = [row] if type(row) not in (list, tuple) else row
        for index, col in enumerate(row):
            if max_len[index] < len(str(col)):
                max_len[index] = len(str(col))
    output = '-' * (sum(max_len) + 1) + '\n'
    output += '|' + ''.join([h + ' ' * (l - len(h)) + '|' for h, l in zip(header, max_len)]) + '\n'
    output += '-' * (sum(max_len) + 1) + '\n'
    for row in iterable:
        row = [row] if type(row) not in (list, tuple) else row
        output += '|' + ''.join([str(c) + ' ' * (l - len(str(c))) + '|' for c, l in zip(row, max_len)]) + '\n'
    output += '-' * (sum(max_len) + 1) + '\n'
    return output

'''
# print(get_pretty_table(uncompliant_ec2_list, ['Instance ID     |||   IP Address']))