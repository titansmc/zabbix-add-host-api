#
#   Zabbix-create-host-api is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>
#

import requests
import json
import sys
from requests.auth import HTTPBasicAuth
import datetime
import time
import config
import getpass

def check_input():
    print 'This is what we get from you:'
    print ''
    print 'Service name: '+hostname
    print 'Host name: '+host_dns
    print 'SSL port: '+ssl_port
    print 'Hostgroup ID: '+host_group_id
    print 'Zabbix Username: '+zabbix_username
    print 'Template ID: '+template_id
    print 'API URL: '+url
    print ''
    print 'Are you sure that you want to add the following?'
    confirm=confirm_choice()
    if confirm == True:
        print 'Go ahead....'
    else:
        print 'Alright... Bye Bye'
        sys.exit(1)

def confirm_choice():
    answer = ""
    while answer not in ["n","y"]:
        answer = raw_input("OK to push to continue [Y/N]? ").lower()
    return answer == "y"


if ( len(sys.argv) < 3 ):
        print 'Usage:'
        print ''
        print '[user@server]# python zabbix_create_host_api.py [hostname-service-name] [host_dns] [ssl_port]'
        print ''
        print 'Note that third paramether is optional, use it if monitoring cert in a non default port 443'
        sys.exit(1)
else:
        hostname=sys.argv[1]
        host_dns=sys.argv[2]
        zabbix_username=raw_input("Insert your Zabbix username:")
        zabbix_password=getpass.getpass()

        # If port not supplied
        if ( len(sys.argv) <= 3):
            ssl_port='443'
            host_group_id=config.host_group_id
            http_auth_username="notneeded"
            http_auth_password="notneeded"
            template_id=config.template_id
            url=config.zabbix_url

            check_input()
        else:
            ssl_port=sys.argv[3]
            host_group_id=config.host_group_id
            http_auth_username="notneeded"
            http_auth_password="notneeded"
            template_id=config.template_id
            url=config.zabbix_url

            check_input()



headers = {'content-type': 'application/json'}
def get_aut_key():
        payload= {'jsonrpc': '2.0','method':'user.login','params':{'user':zabbix_username,'password':zabbix_password},'id':'1'}
        r = requests.post(url, data=json.dumps(payload), headers=headers, verify=True, auth=HTTPBasicAuth(http_auth_username,http_auth_password))
        if  r.status_code != 200:
                print 'problem -key'
                print r.status_code
                print r.text
                sys.exit()
        else:
                result=r.json()
                auth_key=result['result']
                return auth_key

def add_macro(auth_key, host_id):
    payload={
            "jsonrpc": "2.0",
            "method": "usermacro.create",
            "params": {
                "hostid": host_id,
                "macro": "{$SSL_PORT}",
                "value": ssl_port
            },
            "auth": auth_key,
            "id": 1
    }
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=True, auth=HTTPBasicAuth(http_auth_username,http_auth_password))
    if  r.status_code != 200:
        print 'Problem -request when adding macro'
        sys.exit()
    else:
        try:
            result=r.json()['result']
        except:
            result=r.json()['error macro']
            print 'error'
            print result
            sys.exit()


def create_host(auth_key):
        payload={
            "jsonrpc": "2.0",
            "method": "host.create",
            "params": {
                "host": hostname,
                "interfaces": [
                    {
                        "type": 1,
                        "main": 1,
                        "useip": 0,
                        "ip": "",
                        "dns": host_dns,
                        "port": "10050"
                    }
                ],
                "groups": [
                    {
                        "groupid": host_group_id
                    }
                ],
                "templates": [
                    {
                        "templateid": template_id
                    }
                ],
            },
            "auth": auth_key,
            "id": 1
        }



        r = requests.post(url, data=json.dumps(payload), headers=headers, verify=True, auth=HTTPBasicAuth(http_auth_username,http_auth_password))
        if  r.status_code != 200:
                print 'problem -request'
                sys.exit()
        else:
                try:
                        result=r.json()['result']
                        host_id=result['hostids'][0]
                        return host_id
                except:
                        result=r.json()['error']
                        print 'error - creating host'
                        print result
                        sys.exit()


def set_maintenance(auth_key, host_id):
        active_since=int(time.time())
        active_till=int(time.time()+600)

        payload={
            "jsonrpc": "2.0",
            "method": "maintenance.create",
            "params": {
                "name": 'Adding new SSL monitoring service untill (Through zabbix script)'+str(active_till),
                "hostids": [ host_id ],
                "active_since": active_since, 
                "active_till": active_till,
                "timeperiods": [
                    {
                        "timeperiod_type": 0,
                        "period": 1800
                    }
                ]
            },
            "auth": auth_key,
            "id": 1
        }



        r = requests.post(url, data=json.dumps(payload), headers=headers, verify=True, auth=HTTPBasicAuth(http_auth_username,http_auth_password))
        if  r.status_code != 200:
                print 'Problem -request'
                sys.exit()
        else:
                try:
                        result=r.json()['result']

                except:
                        result=r.json()['error']
                        print 'Error, not able to set maintenance.'
                        print result
                        sys.exit()

###########################
# Main program starts here#
###########################

auth_key=get_aut_key()
host_id=create_host(auth_key)
set_maintenance(auth_key,host_id)

# If the SSL port is passed, we run the add macro function
if len(sys.argv) == 4:
    print 'SSL_PORT specified, adding macro.'
    add_macro(auth_key,host_id)
else:
    print 'We didn\'t specified SSL_PORT, therefore not adding macro and the script will default to 443.'



