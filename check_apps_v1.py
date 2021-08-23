import json
import requests
import re
import sys
import datetime
import subprocess

server  = 'https://<phantom host>'
header_template = {
  "Cache-Control": "no-cache, no-store, must-revalidate",
  "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
}

requests.packages.urllib3.disable_warnings()

#############################################
### Send to Slack Function
#############################################
def slack( message ):
  message = {"text": message}
  slack_command = """curl -X POST -H 'Content-type: application/json' --data "{0}" https://hooks.slack.com/services/<slack endpoint>""".format( message )
  process = subprocess.call( slack_command, shell=True )

#############################################
### Initialize Session
#############################################
session = requests.session()
session.headers.update( header_template )
print( datetime.datetime.now() )

#############################################
### Get CSRF from login page
#############################################
print( 'Getting login page' )
login_url = '{}/login'.format(server)
response = session.get(login_url, verify=False)
print(response)
search_string = re.compile( 'name="csrfmiddlewaretoken" value="(.+?)"' )
token = None
for match in re.findall( search_string, response.text ):
  token = str(match)
  break

#############################################
### Login with creds and token
#############################################
print( 'Logging in' )
session.headers.update({"referer": "{}/login".format( server ) })
payload = {
        'username': '<creds>',
        'password': '<creds>',
        'csrfmiddlewaretoken': token
        }
response = session.post(login_url, data=payload, verify=False)
print( response )

#############################################
### Get install version
#############################################
print( 'Get Phantom Version Strings' )
version_url = '{}/rest/version'.format( server )
response = session.get(version_url, verify=False)
version = json.loads(response.text)['version']
print( version )
short_version = version.split( '.' )
short_version = "{}.{}".format( short_version[0], short_version[1] )
print( short_version )

#############################################
### Request App Data
#############################################
print( 'Processing App Data' )
session.headers.update({"x-csrftoken": session.cookies['csrftoken'] })
data = '{{"phantom_version":"{}","current_apps":"[]"}}'.format( version )
print( data )
app_url = '{}/new_portal_apps'.format( server )
response = session.post(app_url, data=data, verify=False)
print( response)

#############################################
### Build App Lookup
#############################################
apps = json.loads( response.text )['result']
lookup = {}
for app in apps:
  lookup[app['app_guid']] = app

###########################################################
### Get app cache
###########################################################
app_cache = None
try:
  file = open("/tmp/app_cache1","r+")
  app_cache = json.loads( file.read() )
except:
  file = open("/tmp/app_cache1","w+")
  file.write( json.dumps( lookup ) )
  file.close()
  sys.exit( 0 )

###########################################################
### Identify new content
###########################################################
new = []
updated = []
for entry in lookup:
  #print( 'processing {}'.format( lookup[entry]['app_name'] ) )
  if entry not in app_cache:
      new.append( 'New app available: {}'.format( lookup[entry]['app_name'] ) )
  elif lookup[entry]['app_version'] != app_cache[entry]['app_version']:
      log_url = "https://repo.phantom.us/phantom/{}/apps/x86_64/{}-release_notes.html".format( short_version, lookup[entry]['app_package_name'] )
      updated.append( '{} app has been updated to {}\nChange Log:\n{}'.format( lookup[entry]['app_name'], lookup[entry]['app_version'], log_url ) )

###########################################################
### Write app cache
###########################################################
try:
  file = open("/tmp/app_cache1","w+")
  file.write( json.dumps( lookup ) )
  file.close()
except:
  pass

###########################################################
### Send info to slack
###########################################################
if not new and not updated:
  print( "No new or updated apps" )
else:
  for entry in new:
    print( entry )
    slack( entry )
  for entry in updated:
    print( entry )
    slack( entry )
