import json
import sys
f = open ("namefile.json", "r")

data = json.load(f)
unique = {each['id'] : each for each in data ['vulnerabilities']}.values()
severity = [{'severity': item['severity'], 'id' : item ['id'], 'exploit': item ['exploit']} for item in unique]
print(severity)
for item in severity:
    if item['exploit'] == 'Functional' and item['severity'] != 'medium':
        sys.exit(1)
