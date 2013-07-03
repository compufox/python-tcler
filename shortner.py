#
#
# Copyright (c) 2013, theZacAttacks
#
# uses the goo.gl API to get shortened links
#

import urllib2
import json
from Tkinter import END

URL = "https://www.googleapis.com/urlshortener/v1/url?"
KEY = "key="


class Shorten():
    def __init__(self, apikey, entry=None):
        self.entry = entry
        self.url = URL + KEY + apikey
        self.header = {'Content-Type': 'application/json'}

    def getShortLink(self, link):
        req = urllib2.Request(self.url,
                              json.dumps({"longUrl": link}),
                              self.header)
        f = urllib2.urlopen(req)
        response = json.loads(f.read())
        f.close()
        return response['id']

    def getLink(self):
        if self.entry is not None:
            text = self.entry.get()
        else:
            text = raw_input("Link to shorten? ")
        if (
            text.split('http')[0] == '' or
            text.split('https')[0] == ''
        ):
            return self.getShortLink(text)
        else:
            return "ERR"

    def placeText(self, text, location=None):
        if self.entry is not None:
            self.entry.delete(0, END)
            self.entry.insert(0, text)
        else:
            print text

    def addEntry(self, entry):
        if entry is not None:
            self.entry = entry
        else:
            print "Entry cannot be None"

    def getLongLink(self, link):
        req = urllib2.Request(URL + "shortUrl=" + link)
        f = urllib2.urlopen(req)
        response = json.loads(f.read())
        f.close()
        return response['longUrl']
