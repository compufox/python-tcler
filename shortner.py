#
#
# Copyright (c) 2013, theZacAttacks
#
# uses the goo.gl API to get shortened links
#

import urllib2
import json
from Tkinter import END, INSERT

class Shorten():
    def __init__(self, entry):
        self.entry = entry
        self.url = "https://www.googleapis.com/urlshortener/v1/url?key=AIzaSyCup5SNezq62uKQQQHQoFTmqKAGnJDoq-A"
        self.header = {'Content-Type': 'application/json'}
        
    def getShortLink(self, link):
        req = urllib2.Request(self.url, json.dumps({"longUrl": link}), self.header)
        f = urllib2.urlopen(req)
        response = json.loads(f.read())
        f.close()
        return response['id']
        
    def getLink(self):
        text = self.entry.get()
        if (
            text.split('http')[0] == '' or
            text.split('https')[0] == ''
        ):
            self.placeText(self.getShortLink(text))
        else:
            return "ERR"
        
    def placeText(self, text):
        self.entry.delete(0, END)
        self.entry.insert(0, text)
