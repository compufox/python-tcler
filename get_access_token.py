#!/usr/bin/python2.4
#
# Copyright 2007 The Python-Twitter Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import sys
import Tkinter

# parse_qsl moved to urlparse module in v2.6
try:
  from urlparse import parse_qsl
except:
  from cgi import parse_qsl

import oauth2 as oauth

def click(event=None):
  import webbrowser as webb
  webb.open(LINK)

def getInfo():
  pincode = entry.get()
  
  token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
  token.set_verifier(pincode)
  
  oauth_client  = oauth.Client(oauth_consumer, token)
  resp, content = oauth_client.request(ACCESS_TOKEN_URL, method='POST', body='oauth_callback=oob&oauth_verifier=%s' % pincode)
  access_token  = dict(parse_qsl(content))
  
  if resp['status'] != '200':
    print 'The request for a Token did not succeed: %s' % resp['status']
    print access_token
  else:
#    print 'Your Twitter Access Token key: %s' % access_token['oauth_token']
#    print '          Access Token secret: %s' % access_token['oauth_token_secret']
#    print ''
    writeInfo(access_token['oauth_token'], access_token['oauth_token_secret'])
    
    root.destroy()

def writeInfo(key, secret):
  open(os.path.expanduser('~/.tcler'), 'w+').write(key + '\n' + secret)

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL  = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL        = 'https://api.twitter.com/oauth/authenticate'

root = Tkinter.Tk()

consumer_key    = 'qJwaqOuIuvZKlxwF4izCw'
consumer_secret = '53dJ9tHJ77tAE8ywZIEU60JYPyoRU9jY2v0d58nI8'

signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()
oauth_consumer             = oauth.Consumer(key=consumer_key, secret=consumer_secret)
oauth_client               = oauth.Client(oauth_consumer)

print 'Requesting temp token from Twitter'

resp, content = oauth_client.request(REQUEST_TOKEN_URL, 'GET')

if resp['status'] != '200':
  print 'Invalid respond from Twitter requesting temp token: %s' % resp['status']
else:
  request_token = dict(parse_qsl(content))

#  print ''
#  print 'Please visit this Twitter page and retrieve the pincode to be used'
#  print 'in the next step to obtaining an Authentication Token:'
#  print ''
#  print '%s?oauth_token=%s' % (AUTHORIZATION_URL, request_token['oauth_token'])
#  print ''
  
  label = Tkinter.Text(root)
  label.insert(1.0, 'If your browser didn\'t open please visit this Twitter page and retrive the pincode to be entered in below:\n' )
  
  label.tag_config("a", foreground="blue", underline=1)
  label.tag_bind("a", "<Button-1>", click)
  
  label.insert(2.0, '%s?oauth_token=%s' % (AUTHORIZATION_URL, request_token['oauth_token']), "a")
  label.pack(side=Tkinter.LEFT)
  
  global LINK
  LINK = '%s?oauth_token=%s' % (AUTHORIZATION_URL, request_token['oauth_token'])
  
  entry = Tkinter.Entry(root)
  entry.pack(side=Tkinter.BOTTOM)
  
  button = Tkinter.Button(root,text='Submit', command=getInfo)
  button.pack(side=Tkinter.RIGHT)
  


#  print ''
#  print 'Generating and signing request for an access token'
#  print ''

#  oauth_client  = oauth.Client(oauth_consumer, token)
#  resp, content = oauth_client.request(ACCESS_TOKEN_URL, method='POST', body='oauth_callback=oob&oauth_verifier=%s' % pincode)
#  access_token  = dict(parse_qsl(content))

#  if resp['status'] != '200':
#    print 'The request for a Token did not succeed: %s' % resp['status']
#    print access_token
#  else:
#    print 'Your Twitter Access Token key: %s' % access_token['oauth_token']
#    print '          Access Token secret: %s' % access_token['oauth_token_secret']
#    print ''

click()

root.mainloop()