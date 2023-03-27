from __future__ import print_function
import json
import urllib
import boto3
import gzip
import io
s3 = boto3.client('s3')
sns = boto3.client('sns')
SNS_ARN = 'arn:aws:sns:ap-northeast-2:132323974198:ec2taggingmonitor'
TAGS = ['production', 'development']

def decompress(data):
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:
        return f.read()

def report(instance, user, region):
    report = "User " + user + " created an instance with non-compliant tag in the region " +  region + ". \n"
    report += "Instance id: " + instance['instanceId'] + "\n"
    report += "Instance type: " + instance['instanceType'] + "\n"
    report += "The instance is being destroyed."
    return report

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    try:
        s3_object = s3.get_object(Bucket=bucket, Key=key)
        s3_object_content = s3_object['Body'].read()
        s3_object_unzipped_content = decompress(s3_object_content)
        json_object = json.loads(s3_object_unzipped_content)
        for record in json_object['Records']:
            if record['eventName'] == "RunInstances":
                user = record['userIdentity']['userName']
                region = record['awsRegion']
                ec2 = boto3.resource('ec2', region_name=region)
                for index, instance in enumerate(record['responseElements']['instancesSet']['items']):
                    instance_object = ec2.Instance(instance['instanceId'])
                    tags = {}
                    for tag in instance_object.tags:
                        tags[tag['Key']] = tag['Value']
                    if('Purpose' not in tags or tags['Purpose'] not in TAGS):
                        instance_object.terminate()
                        sns.publish(TopicArn=SNS_ARN, Message=report(instance, user, region))
    except Exception as e:
        print(e)
        raise e