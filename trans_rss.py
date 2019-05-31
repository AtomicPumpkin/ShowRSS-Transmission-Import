#!/usr/bin/python3
## Required
## pip3 install feedparser
## pip3 install requests

import feedparser
import requests
import json
from datetime import datetime, timedelta
from time import mktime
from requests.auth import HTTPBasicAuth

#######################
#        Config       #
#######################
# Debug logging adds start and stop log entries to 
# confirm cron job is working as expected
debugLogging = True

# Transmission RPC Details
rpcHost = ''                    # IP or hostname of your transmission server
rpcPort = 22974                 # Standard RPC port = 22974
rpcUser = ''                    # Your transmission user
rpcPass = ''                    # Your transmission password
rpcPath = '/transmission/rpc'   # Path to RPC, should be /transmission/rpc

# Link to your showRSS feed
# https://showrss.info
feedURL = ""

# Log File
logFile = 'log.txt'

# Limit new additions to entries in the last [x] days
# trasmission server handles duplicate entry attempts for us
dayOffset = 7

#######################
#     End Config      #
#######################

rpcUrl = 'http://'+rpcHost+':'+str(rpcPort)+rpcPath

# Get RPC Session ID
# Required by Transmission to Mitigate CSRF
def get_rpc_session():
    sessionRequest = requests.get(rpcUrl, auth=(rpcUser, rpcPass), verify=False)
    return sessionRequest.headers['x-transmission-session-id']

# Post Magnet Link to Transmission
def add_magnet(magnetLink):
    sessionid = get_rpc_session()
    if sessionid:
        errorText = ''
        postHeader = {"X-Transmission-Session-Id": sessionid}
        postBody = json.dumps({"method": "torrent-add", "arguments": {"filename": magnetLink}})
        postRequest = requests.post(rpcUrl, data=postBody, headers=postHeader, auth=(rpcUser, rpcPass), verify=False)
        postResponse = json.loads(postRequest.text)
        if postResponse['result'] == 'success':
            if('torrent-duplicate' in postResponse['arguments']):
                return 'torrent-duplicate '+postResponse['arguments']['torrent-duplicate']['name']
            return True
        else:
            return str(postResponse)

logDatetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
dateLimit = datetime.now() - timedelta(days=dayOffset)
dateLimit = dateLimit.strftime("%Y%m%d")

rss = feedparser.parse(feedURL)
rssEntries = rss.entries

fileHandle = open(logFile,"a")

if debugLogging == True:
    fileHandle.write('%s | Cron Start \r\n'%(logDatetime))

for entry in rss.entries:
    magnetTitle = entry.title
    magnetLink = entry.link
    datePublished = datetime.fromtimestamp(mktime(entry.published_parsed)).strftime("%Y%m%d")

    if datePublished >= dateLimit:
        sendMagnet = add_magnet(magnetLink)
        if sendMagnet == True:
            fileHandle.write('%s | Added: %s \r\n'%(logDatetime,magnetTitle))
        else:
            fileHandle.write('%s | Failed: %s \r\n'%(logDatetime,sendMagnet))

if debugLogging == True:
    fileHandle.write('%s | Cron End \r\n'%(logDatetime))