#!/usr/bin/env python2
#
# Zachary Epps, 2013
#
# A simple little twitter client written using the python-twitter
#  module and tcl for a GUI.
#
# Version       Changelog
#-------------------------------------------------------------------------------
# 0.1           original tcl gui code written
#
# 0.2           got the unique api code hardcoded
#
# 0.4           added threads to improve GUI performace
#
# 0.6           changed a lot of the display code to make it more
#                robust and applicable
#
# 0.8           can pull tweets from timeline, can post tweets
#                tweet's author is easily distenguished from tweets
#
# 0.9           tweets displayed accuratly, autoupdating works and 
#                character counting works
#
# 0.9.1         GUI resizes correctly, and took out the hard coded
#                values of my creds and made it check ~/.tcler for
#                the user's key & token. 
#               IDEAS: make links clickable. scan through each tweet
#                that comes in, and make each hyperlink clickable. (DONE)
#
# 0.9.2         Links now clickable, added menu item to open every link
#                Fixed the new tweet display error
#
# 0.9.3         Added some error handling for character for the Tkinter 
#                Text widget
#
# 0.9.4         Added a console option. This prints out the errors/thread
#                info that typically gets printed to the console to a 
#                GUI window for users not running from console

from Tkinter import *
from os import path
import twitter
import threading
from urllib2 import URLError
from time import sleep
import tkHyperlinkManager

global STREAM_UPDATE
STREAM_UPDATE = True

global LAST_ID
LAST_ID = None

global TEXT
TEXT = None

global CON
CON = None

class conDialog(Toplevel):
        def __init__(self, parent, title):
                self.top = Toplevel(parent)
                self.top.wm_title(title)
                self.top.wm_minsize(width=200, height=250)
                
                self.parent = parent
                
                self.running = True
                
                self.logger = Text(self.top, width=30, height=15)
                self.logger.pack(fill=BOTH, expand=1)
                
                self.close = Button(self.top, text="Close", command=self.closeThisWindow)
                self.close.pack(fill=X,expand=0)
                
                self.logger.config(state=DISABLED)

        def closeThisWindow(self):
                self.top.destroy()
                global CON
                CON = None
                
        def placeText(self, errors):
                self.logger.config(state=NORMAL)
                self.logger.insert(INSERT, errors)
                self.logger.config(state=DISABLED)

class upThread (threading.Thread):
        def __init__(self, threadID, name, args):
                threading.Thread.__init__(self)
                self.threadID = threadID
                self.name = name
                
                if name == "update":
                        self.tweet_id = args
                elif name == "numbers":
                        self.entry = args
                elif name == "post":
                        self.tweet_id = args
                
        def run(self):
#                if CON != None:
#                        CON.placeText(self.name + " starting...\n")
#                else:
                print(self.name + " starting...")
                if self.name == "update":
                        if self.tweet_id != 1:
                                update(0, self.tweet_id)
                        else:
                                update(1,LAST_ID)
                elif self.name == "numbers":
                        numbers(self.entry)
                elif self.name == "post":
                        post()
#                if CON != None:
#                        CON.placeText(self.name + " exiting...\n")
#                else:
                print(self.name + " exiting...")
        def getName(self):
                return(self.name)
        

# updates the text in the text widget with supplied tuple(?) of
#  statuses. 
#
#  DO NOT CHANGE
def updateDisplay(status):
        text.config(state=NORMAL)
        
        newStat = "< > "
        counter = 1.0
        
        text.insert(counter, "\n")
        
        for s in reversed(status):
                try:
                        if s != status[0]:
                                newStat = "\n<" + s.user.screen_name + "> "
                        else:
                                newStat = "<" + s.user.screen_name + "> "
                        length = len(newStat)/100
                        for word in reversed(s.text.split(' ')):
                                if word.split(':')[0] == 'http' or word.split(':')[0] == 'https':
                                        text.insert(counter, " ")
                                        text.insert(counter, word, hyper.add(openLink, word))
                                else:
                                        text.insert(counter, word + " ")
#                                text.insert(counter+len(s.text),"\n")
                        text.insert(counter, newStat, "a")
                                
                except TclError:
                        if CON != None:
                                CON.placeText("A Tcl Character error occured, the offending tweet wasn't displayed\n")
                        else:
                                print "A Tcl Character error occured, the offending tweet wasn't displayed"
        
        text.config(state=DISABLED)


# starts a thread that runs a one-shot update on statuses.
#  this method, like the postThread method, is mainly
#  so the GUI doesn't freeze up while the method runs
def oneShotUpdate():
        one_update = upThread(3, "update", 1)
        one_update.start()

# supplies the callback to open links in the default
#  web browser
def openLink(link):
        import webbrowser as webb
        webb.open(link)

# shows the console
def showConsole():
        if CON != None:
                CON.placeText("Console already shown\n")
        else:
                global CON
                CON = console = conDialog(root, "Console")

# posts the status updates
def post():
        toPost = entry.get()
        entry.delete(0, END)
        
        api.PostUpdate(toPost)

# keeps track of the chacter count and updates the GUI label 
def numbers(entry):
        while STREAM_UPDATE:
                global TEXT
                TEXT.set(140 - len(entry.get()))
                sleep(.1)

# quits the threads
def quit(thread):
        global STREAM_UPDATE
        STREAM_UPDATE = False
        thread.join()
        
        if CON != None:
                CON.top.destroy()
        
        sys.exit()

# starts a thread to run the post function. (Made this just so the GUI 
#   doesn't unattractivly freeze up
def postThreader():
        post_thread = upThread(2,"post",0)
        post_thread.start()

# gets the newest updates, while trying to stay within the Twitter's API
#   rate limit. has two modes, 0 and 1. 1 is just a one time thing, while
#   0 drops into a loop that checks every minute for new updates. 0 is meant
#   for the update thread and nothing else, while 1 is meant for the update
#   button.
def update(shot, last_id):
        if shot != 1:
                counter = 0
                while STREAM_UPDATE:
                        STATUSES = list()
                        try:
                                STATUSES = api.GetHomeTimeline(since_id=last_id)
                                if len(STATUSES) != 0:
                                        last_id = STATUSES[0].id
                                
#                                if counter == 15 or counter > 15:
#                                        STATUSES = ()
#                                        counter = 0
#                                        sleep(60*14)
                                
                                if len(STATUSES) > 0 and LAST_ID != last_id:
                                        global LAST_ID
                                        LAST_ID = last_id
                                        updateDisplay(STATUSES)
                                
                                for i in range(18):
                                        sleep(5)
                                        if STREAM_UPDATE != True:
                                                break
                                                
                                if STREAM_UPDATE != True:
                                        break
                                counter += 1
                        except twitter.TwitterError:
                                if CON != None:
                                        CON.placeText("There was a Twitter problem getting the tweets\n")
                                else:
                                        print "There was a Twitter problem getting the tweet"
                                for i in range(18):
                                        sleep(5)
                                        if STREAM_UPDATE != True:
                                                break
                                                
                                if STREAM_UPDATE != True:
                                        break
                        except URLError:
                                if CON != None:
                                        CON.placeText("There was a network issue when getting the tweets\n")
                                else:
                                        print "There was a network issue when getting the tweets"
                                for i in range(18):
                                        sleep(5)
                                        if STREAM_UPDATE != True:
                                                break
                                                
                                if STREAM_UPDATE != True:
                                        break
                        
        else:
                try:
                        STATUSES = ()
                        STATUSES = api.GetHomeTimeline(since_id=last_id)
                
                        if len(STATUSES) > 0:
                                global LAST_ID
                                LAST_ID = STATUSES[0].id
                                updateDisplay(STATUSES)
                except twitter.TwitterError:
                        if CON != None:
                                CON.placeText("There was a Twitter problem getting the tweets\n")
                        else:
                                print "There was a Twitter problem getting the tweet"
                except URLError:
                        if CON != None:
                                CON.placeText("There was a network issue when getting the tweets\n")
                        else:
                                print "There was a network issue when getting the tweets"

ASS_KEY = None
ASS_SECRET = None

if not path.exists(path.expanduser('~/.tcler')):
       import get_access_token

red = open(path.expanduser('~/.tcler'), 'r').read().split('\n')
ASS_KEY = red[0]
ASS_SECRET = red[1]

# get the API reference
api = twitter.Api(consumer_key='qJwaqOuIuvZKlxwF4izCw',
		  consumer_secret='53dJ9tHJ77tAE8ywZIEU60JYPyoRU9jY2v0d58nI8',
		  access_token_key=ASS_KEY,
		  access_token_secret=ASS_SECRET)

# no errors! yet
ERR = None

# no statuses either
STATUSES = None

# try and get the statuses, while catching either a network error 
#  or a twitter error
try:
        STATUSES = api.GetHomeTimeline()
        
#        global LAST_ID
#        LAST_ID = STATUSES[0].id
except URLError:
        print "Uh-oh"
        ERR = "There was a problem opening the network connection. Please ensure that your computer is online."
except twitter.TwitterError:
        ERR = "Your timeline could not be retrieved at this time.\nPlease try again later."

# tries to start a thread that just constantly runs the update function
#  (see the update function docs for more info)
try:
        UPDATE_THREAD = upThread(0, "update", LAST_ID)
        
        UPDATE_THREAD.start()
except:
        print("Error: threads are hard!")

# 
# STARTS SETTING UP TK GUI STUFF
#
root = Tk()
root.wm_title("Python Tcler - Twitter Client")
root.wm_minsize(width=200,height=400)

global TEXT
TEXT = StringVar(root)

scroll = Scrollbar(root)
scroll.pack(side=RIGHT, fill=Y,expand=0)

text = Text(root, yscrollcommand=scroll.set)
text.config(state=DISABLED, wrap=WORD)
text.pack(fill=BOTH, expand=1)
text.tag_config("a", foreground="red")

hyper = tkHyperlinkManager.HyperlinkManager(text)

post_button = Button(root, text="Post", command=postThreader)
post_button.pack(side=RIGHT, fill=BOTH, expand=0)

Label(root, textvariable=TEXT).pack(side=RIGHT)

entry = Entry(root)
entry.pack(fill=X, expand=1 ,side=RIGHT)

#update_button = Button(root, text='Update', command=oneShotUpdate)
#update_button.pack(side=RIGHT)

#quit_button = Button(root, text='Quit', command=lambda: quit(UPDATE_THREAD))
#quit_button.pack(side=LEFT)

scroll.config(command=text.yview)

menu = Menu(root)
menu.add_command(label="Update", command=oneShotUpdate)
menu.add_command(label="Console", command=showConsole)
menu.add_command(label="Quit", command=lambda: quit(UPDATE_THREAD))
root.config(menu=menu)

if ERR != None:
        text.config(state=NORMAL)
        text.insert(1.0, ERR)

#
# END OF TK GUI STUFF
#

# tries to start a thread that will keep the character count
#  see the docs on the numbers function
try:
        NUMBER_THREAD = upThread(1, "numbers", entry)
        NUMBER_THREAD.start()
except:
        print("Well, no character count...")

root.mainloop()
