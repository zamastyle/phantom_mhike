import sys
import requests
import json
import re
import io
import gzip
import xml.etree.ElementTree as ET
import subprocess
import datetime

requests.packages.urllib3.disable_warnings()

AUTH_TOKEN = '<auth token>'
server  = 'https://<phantom host>'
headers = {
  "ph-auth-token": AUTH_TOKEN,
  "Cache-Control": "no-cache, no-store, must-revalidate",
}

###########################################################
### Function: Send Data to Slack Channels
###########################################################
def slack(message):
  message = {"text": message}
  mhike_slack = 'https://hooks.slack.com/services/<slack endpoint>'
  response = requests.post(mhike_slack, data=json.dumps(message), verify=False)
  print(response)

print( '\n' + str(datetime.datetime.now()) )

###########################################################
### Get Phantom Version
###########################################################
version_url = '{}/rest/version'.format(server)
response = requests.get(version_url, headers=headers, verify=False)
version = json.loads(response.text)['version']
print(version)
short_version = version.split('.')
short_version = "{}.{}".format(short_version[0], short_version[1])
print(short_version)

###########################################################
### Build New App Lookup From Repo Data
###########################################################
app_lookup = {}
pattern = re.compile('href="(.*?-primary.xml.gz)"')
response = requests.get("https://repo.phantom.us/phantom/{}/apps/x86_64/repodata/".format(short_version))
print(response)
inventory = None
for match in re.findall(pattern, response.text):
  inventory = str(match)
  break
if inventory:
  response = requests.get('https://repo.phantom.us/phantom/{}/apps/x86_64/repodata/{}'.format(short_version,inventory))
  print(response)
  compressed_file = io.BytesIO(response.content)
  inventory_xml = io.BytesIO(gzip.open(compressed_file).read())
  xml_tree = ET.parse(inventory_xml)
  root = xml_tree.getroot()
  for package in root.findall('{http://linux.duke.edu/metadata/common}package'):
    package_data = {}
    package_data['name'] = package.find('{http://linux.duke.edu/metadata/common}summary').text
    package_data['package'] = package.find('{http://linux.duke.edu/metadata/common}name').text
    package_data['description'] = package.find('{http://linux.duke.edu/metadata/common}description').text
    package_data['version'] = package.find('{http://linux.duke.edu/metadata/common}version').attrib['ver']
    if package_data['package'] in app_lookup:
      lookup_version = app_lookup[package_data['package']]['version'].split('.')
      new_version = package_data['version'].split('.')
      i = 0
      for entry in lookup_version:
        if int(entry) < int(new_version[i]):
          app_lookup[package_data['package']] = package_data
          break
        i += 1
    else:
      app_lookup[package_data['package']] = package_data

###########################################################
### Get app cache
###########################################################
app_cache = None
try:
  file = open("/tmp/app_cache","r+")
  app_cache = json.loads(file.read())
except:
  file = open("/tmp/app_cache","w+")
  file.write(json.dumps(app_lookup))
  file.close()
  sys.exit(0)

###########################################################
### Identify new content
###########################################################
new = []
updated = []
for entry in app_lookup:
  if entry not in app_cache:
      new.append('> New app available: *{}*\n'.format(app_lookup[entry]['name']))
  elif app_lookup[entry]['version'] != app_cache[entry]['version']:
      log_url = "https://repo.phantom.us/phantom/{}/apps/x86_64/{}-release_notes.html".format(short_version, app_lookup[entry]['package'])
      updated.append('> Updated app: *{}*```{} app has been updated to {}\nChange Log:\n{}\n```'.format(app_lookup[entry]['name'],app_lookup[entry]['name'], app_lookup[entry]['version'], log_url))

###########################################################
### Write app cache
###########################################################
try:
  file = open("/tmp/app_cache","w+")
  file.write(json.dumps(app_lookup))
  file.close()
except:
  pass

###########################################################
### Send info to slack
###########################################################
if not new and not updated:
  print("No new or updated apps")
else:
  for entry in new:
    print(entry)
    slack(entry)
  for entry in updated:
    print(entry)
    slack(entry)
