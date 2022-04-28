import sys
import requests
import json
import re
import datetime

requests.packages.urllib3.disable_warnings()


###########################################################
### Function: Send Data to Slack Channels
###########################################################
def slack(message):
  message = {"text": message}
  comm_slack = '<slack webhook>'
  response = requests.post(comm_slack, data=json.dumps(message), verify=False)
  print(response)


CLEANR = re.compile('<.*?>')
BULLETS = re.compile('\s*-----\s*')

def cleanhtml(raw_html):
  raw_html = raw_html.replace('\n', ' ')
  raw_html = raw_html.replace('<p>', '')
  raw_html = raw_html.replace('</p>', '')
  raw_html = raw_html.replace('<span>', '')
  raw_html = raw_html.replace('</span>', '')
  raw_html = raw_html.replace('<li>', '-----')
  raw_html = raw_html.replace('</li>', '')
  while '  ' in raw_html:
    raw_html = raw_html.replace('  ', ' ')
  cleantext = re.sub(CLEANR, '', raw_html)
  cleantext = cleantext.replace('-----', '\n  - ')
  return cleantext

def get_app_info(sbid):
  print('Getting app details for app id {}'.format(sbid))
  html_response = requests.get('https://splunkbase.splunk.com/app/{0}/'.format(sbid))
  html_data = html_response.text
  action_data = html_data[html_data.index('Supported Actions Version'):]
  action_data = action_data[:action_data.index('</sb-release-select>')]
  action_data = cleanhtml(action_data)
  change_data = html_data[html_data.index('Release Notes'):]
  change_data = change_data[:change_data.index('</sb-release-select>')]
  change_data = cleanhtml(change_data)
  return action_data, change_data

print( '\n' + str(datetime.datetime.now()) )

###########################################################
### Build New App Lookup From Repo Data
###########################################################
app_lookup = {}
page = 0
total = 0
while True:
  response = requests.get("https://splunkbase.splunk.com/api/v2/apps/?offset={0}&limit=20&archive=false&product=soar&include=release,release.version_compatibility".format(page))
  if total == 0:
    total = json.loads(response.text)['total']
  for app_pkg in json.loads(response.text)['results']:
    package_data = {}
    package_data['name'] = app_pkg['app_name']
    package_data['description'] = app_pkg['description']
    package_data['app_id'] = app_pkg['app_id']
    package_data['sbid'] = app_pkg['id']
    package_data['version'] = app_pkg['release']['release_name']
    package_data['compatible_with'] = app_pkg['release']['version_compatibility']
    package_data['changes'] = 'Change Log:{}'.format(cleanhtml(app_pkg['release']['notes']))
    app_lookup[package_data['app_id']] = package_data
  page += 20
  if page > total:
    break

###########################################################
### Get app cache
###########################################################
app_cache = None
try:
  file = open("./app_cache","r+")
  app_cache = json.loads(file.read())
except:
  file = open("./app_cache","w+")
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
      print(f'New app released: {app_lookup[entry]["name"]}')
      new.append((f'> New app available: *{app_lookup[entry]["name"]}*\n'
                  f' Compatible with: {", ".join(app_lookup[entry]["compatible_with"])}\n'
                  f'```{app_lookup[entry]["changes"]}```\n\n'))
  elif app_lookup[entry]['version'] != app_cache[entry]['version']:
      print(f'{app_lookup[entry]["name"]} updated from {app_cache[entry]["version"]} to {app_lookup[entry]["version"]}')
      updated.append((f'> Updated app: *{app_lookup[entry]["name"]}*\n'
                      f'> {app_lookup[entry]["name"]} v{app_lookup[entry]["version"]}\n'
                      f'> Compatible with: {", ".join(app_lookup[entry]["compatible_with"])}\n'
                      f'```{app_lookup[entry]["changes"]}```\n\n'))

###########################################################
### Write app cache
###########################################################
try:
  file = open("./app_cache","w+")
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
    slack(entry)
  for entry in updated:
    slack(entry)
    
