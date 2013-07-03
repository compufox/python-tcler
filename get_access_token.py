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
#
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# MODIFIED BY theZacAttacks for GUI, file, and Windows support
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import cred_man
import Tkinter
import webbrowser

# parse_qsl moved to urlparse module in v2.6
try:
  from urlparse import parse_qsl
except:
  from cgi import parse_qsl

import oauth2 as oauth

global REQ_TOK
REQ_TOK = None

global ENTRY
ENTRY = None


# open the oauth link in a  browser
def click(event=None):
  webbrowser.open(LINK)


# retrieves the pincode from the entry widget
def getInfo(oauth_consumer, root):
  if ENTRY.get() != "":
    pincode = ENTRY.get()
  else:
    pincode = 12345
  token = oauth.Token(REQ_TOK['oauth_token'], REQ_TOK['oauth_token_secret'])
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
  cred_man.addUser(key, secret)

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL  = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL        = 'https://api.twitter.com/oauth/authenticate'


def startLogin():
  
  root = Tkinter.Tk()
  root.wm_title("Authorize this application")
  
  root.wm_maxsize(width=800,height=80)
  root.wm_minsize(width=750,height=80)
  
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
    global REQ_TOK
    REQ_TOK = dict(parse_qsl(content))
  
  label = Tkinter.Text(root, height=4)
  label.insert(1.0, 'If your browser didn\'t open please visit this Twitter page and retrive the pincode to be entered in below:\n' )
  
  label.tag_config("a", foreground="blue", underline=1)
  label.tag_bind("a", "<Button-1>", click)
  
  label.insert(2.0, '%s?oauth_token=%s' % (AUTHORIZATION_URL, REQ_TOK['oauth_token']), "a")
  label.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH, expand=0)
  
  global LINK
  LINK = '%s?oauth_token=%s' % (AUTHORIZATION_URL, REQ_TOK['oauth_token'])
  
  global ENTRY
  ENTRY = Tkinter.Entry(root)
  ENTRY.pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH)
  
  button = Tkinter.Button(root,text='Submit', command=lambda: getInfo(oauth_consumer, root))
  button.pack(side=Tkinter.RIGHT, fill=Tkinter.BOTH, expand=1)
  
  click()
  
  root.mainloop()
