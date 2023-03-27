import json
import boto3

ec2 = boto3.client('ec2', region_name='eu-west-1')

def lambda_handler(event, context):
    ec2_instances = ec2.describe_instances()
    ec2_reservations = ec2_instances['Reservations']

    for reservation in ec2_reservations:
        instances = reservation['Instances']

        for instance in instances:
            if should_stop_instance(instance):
                stop_instance(instance)


def should_stop_instance(instance):
    should_stop = False

    instance_state = instance['State']['Name']

    for tag in instance['Tags']:
        if tag['key'].lower() == 'tag:testing' and tag['Value'].lower() == 'testinstance' and instance_state == 'running':
            should_stop = True

    return should_stop


def stop_instance(instance):
    instance_id = instance['InstanceId']

    ec2.stop_instances(InstanceIds=[instance_id])
    print("The instance is stopped:" + instance_id)