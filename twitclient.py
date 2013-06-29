#!/usr/bin/env python2
#
# Copyright (c) 2013, theZacAttacks
#
#
# A simple little twitter client written using the python-twitter
#  module and tcl for a GUI.
#
# Version       Changelog
#------------------------------------------------------------------------------
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
#                GUI window for users not running from console. Also
#                https links now work
#               IDEAS: make ERR a list that contains the backlog of errors
#                and/or messages. Make console display the backlog of
#                errors whenever it gets started
#
# 0.9.5         All messages/errors are stored in ERR which is now a global
#                list. When the console is started the backlog of messages
#                (stored in ERR) is vomited into the console. These backlog
#                messages are greyed out, whereas the new messages are
#                not greyed.
#
# 0.9.6         Clicking a user's handle (the text in red) will now fill
#                out the 'post' box with their username, allowing easier
#                tweets at a person. Also, incorporated tkHyperLinkManager
#                into the main file.
#               IDEAS: Make the hashtags clickable which opens a Toplevel
#                box that lists the search results. Incorporate a search
#                function into the client itself, accessable via a menu
#                button.

import twitter
import threading
import webbrowser
import get_access_token

from os import path
from urllib2 import URLError
from time import sleep
from time import localtime
from platform import system

try:
        from Tkinter import (Scrollbar, Text, Entry, Tk, Button, Toplevel,
                             Menu, StringVar, Label, TclError, BOTH,
                             RIGHT, X, Y, NORMAL, DISABLED, WORD, INSERT,
                             END, CURRENT, TOP, LEFT)
except ImportError:
        from tkinter import (Scrollbar, Text, Entry, Tk, Button, Toplevel,
                             Menu, StringVar, Label, TclError, BOTH,
                             RIGHT, X, Y, NORMAL, DISABLED, WORD, INSERT,
                             END, CURRENT, TOP, LEFT)

#
# GLOBAL VARIABLE DECLARATION
#
global SEARCH
SEARCH = None

global ERRORS_SIGS
ERRORS_SIGS = {'twitter': "- Your timeline could not be retrieved at this "
               + "time.\nPlease try again later.",
               'tcl': "- A Tcl Character error occured, "
               + "the offending tweet wasn't displayed",
               'net':  "- There was a problem opening the network "
               + "connection. Please ensure that your computer is online.",
               'console': "- Console already shown",
               'update': "- Streaming update thread failed to start. Updating"
               + " will have to be done manually.",
               'numbers':  "- Starting the thread for numbers failed."
               + " Character counting will not be operational",
               'login': "- Your credential file could not be opened." +
               " Did you login?",
               'generic': "Something has gone wrong, please check the console",
               'search': '- Search window already opened'}

# log of errors
global ERR
ERR = list()

# bool that helps stop the threads
global STREAM_UPDATE
STREAM_UPDATE = True

# the id of the last tweet
global LAST_ID
LAST_ID = {'tweet': 0,
           'self': 0,
           'mention': 0}

# Tkinter StringVar (used for updating the character count
global TEXT
TEXT = None

# conDialog reference that is used for checks
global CON
CON = None


# class that helps handle the task of managing
#  the various 'clicky' actions for text
class HyperlinkManager:
        
        def __init__(self, text):
                self.text = text
                self.text.tag_config("hyper", foreground="blue", underline=1)
                self.text.tag_bind("hyper", "<Enter>", self._enter)
                self.text.tag_bind("hyper", "<Leave>", self._leave)
                self.text.tag_bind("hyper",
                                   "<Button-1>",
                                   lambda x: self._click("hyper"))
                self.text.tag_config("handle", foreground="red")
                self.text.tag_bind("handle",
                                   "<Button-1>",
                                   lambda x: self._click("handle"))
                self.text.tag_config("inlineH", foreground="black")
                self.text.tag_bind("inlineH",
                                   "<Button-1>",
                                   lambda x: self._click("inlineH"))
                self.text.tag_config("hash", foreground="DarkOliveGreen4")
                self.text.tag_bind("hash",
                                   "<Button-1>",
                                   lambda x: self._click("hash"))
                
                self.reset()
        
        def reset(self):
                self.links = {}
        
        def add(self, action, text, thisTag):
                tag = thisTag + "-%d" % len(self.links)
                self.links[tag] = (action, text)
                return thisTag, tag
        
        def _enter(self, event):
                self.text.config(cursor="hand2")
        
        def _leave(self, event):
                self.text.config(cursor="")
        
        def _click(self, thisTag, event=None):
                for tag in self.text.tag_names(CURRENT):
                        if tag[:(len(thisTag) + 1)] == thisTag + "-":
                                self.links[tag][0](self.links[tag][1])
                                return


class searchDialog(Toplevel):
        def __init__(self, parent, title):
                self.top = Toplevel(parent)
                self.top.wm_title(title)
                
                self.searchy = Text(self.top)
                self.searchy.config(wrap=WORD)
                self.search_entry = Entry(self.top)
                self.close = Button(self.top, text="Close", command=self.close)
                self.search_button = Button(self.top, text="Search")
                self.scrollbar = Scrollbar(self.top)
                
                self.scrollbar.pack(side=RIGHT, fill=Y, expand=0)
                self.searchy.config(yscrollcommand=self.scrollbar.set, state=DISABLED)
                self.searchy.pack(side=TOP, fill=BOTH, expand=1)
                self.search_entry.pack(side=LEFT, fill=X, expand=1)
                self.close.pack(side=RIGHT, fill=BOTH, expand=0)
                self.search_button.pack(side=RIGHT, fill=BOTH, expand=0)
                
                self.linker = HyperlinkManager(self.searchy)
                
        def close(self):
                global SEARCH
                SEARCH = None
                self.top.destroy()
        
        def putText(self, text):
                updateDisplay(text, self.searchy, self.linker)

# a small class that allows for a Toplevel widget to
#  become active with the console log
class conDialog(Toplevel):
        def __init__(self, parent, title):
                self.top = Toplevel(parent)
                self.top.wm_title(title)
                self.top.wm_minsize(width=200, height=250)
                
                self.parent = parent
                
                self.logger = Text(self.top, width=50, height=15)
                self.logger.pack(fill=BOTH, expand=1)
                self.logger.config(wrap=WORD)
                
                self.close = Button(self.top, text="Close",
                                    command=self.closeThisWindow)
                self.close.pack(fill=X, expand=0)
                
                self.logger.tag_config('backlog', foreground="grey")
                self.logger.tag_config('ERR', foreground="IndianRed1")
                
                for e in range(len(ERR)):
                        if len(ERR[e][1]) > 1:
                                self.logger.insert(INSERT,
                                                   str(ERR[e][0] + "\n"),
                                                   ERR[e][1])
                        else:
                                self.logger.insert(INSERT,
                                                   str(ERR[e] + '\n'),
                                                   'backlog')
                self.logger.config(state=DISABLED)

        # destroys this Toplevel widget and sets the CON variable to None
        def close(self):
                self.top.destroy()
                global CON
                CON = None
                
        # method that places the text inside the log thats in the console
        #  also stores the messages in the backlog (ERR)
        def placeText(self, message):
                self.logger.config(state=NORMAL)
                ERR.append(message)
                
                if len(message[1]) > 1:
                        self.logger.insert(INSERT,
                                           str(message[0] + "\n"),
                                           message[1])
                else:
                        self.logger.insert(INSERT, message + "\n")
                
                self.logger.config(state=DISABLED)


# class that instantiates a thread which,
#  based off of the name, thread id and arguments does certain jobs
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
                elif name == "hash":
                        self.tweet_id = args
                
        # starts the threads while making a note in the backlog/console
        def run(self):
                if CON is not None and not self.threadID < 2:
                        CON.placeText(getTime()
                                      + "- "
                                      + self.name
                                      + "-"
                                      + str(self.threadID)
                                      + " starting...")
                elif self.threadID < 2:
                        ERR.append(getTime()
                                   + "- "
                                   + self.name
                                   + "-"
                                   + str(self.threadID)
                                   + " starting...")
                elif CON is None and not self.threadID < 2:
                        ERR.append(getTime()
                                   + "- "
                                   + self.name
                                   + "-"
                                   + str(self.threadID)
                                   + " starting...")
                else:
                        print(self.name + " starting...")
                if self.name == "update":
                        if self.tweet_id != 1:
                                update(0, self.tweet_id)
                        else:
                                update(1, LAST_ID['tweet'])
                elif self.name == "numbers":
                        numbers(self.entry)
                elif self.name == "post":
                        post()
                elif self.name == "del":
                        deleteTweet()
                elif self.name == "hash":
                        clickHash(self.tweet_id)
                if CON is not None and not self.threadID < 2:
                        CON.placeText(getTime()
                                      + "- "
                                      + self.name
                                      + "-"
                                      + str(self.threadID)
                                      + " exiting...")
                elif CON is None and not self.threadID < 2:
                        ERR.append(getTime()
                                   + "- "
                                   + self.name
                                   + "-"
                                   + str(self.threadID)
                                   + " exiting...")
                else:
                        print(self.name + " exiting...")
        
        # returns the name of the thread
        def getName(self):
                return(self.name)
        

# updates the text in the text widget with supplied tuple(?) of
#  statuses.
#
#  DO NOT CHANGE, unless you have a good reason
#   (which I always have a good reason)
def updateDisplay(status, tfield, linkman):
        tfield.config(state=NORMAL)
        
        newStat = "< > "
        counter = 1.0
        
        tfield.insert(counter, "\n")
        
        for s in reversed(status):
                try:
                        if s != status[0]:
                                newStat = "\n<" + s.user.screen_name + "> "
                        else:
                                newStat = "<" + s.user.screen_name + "> "
                        
                        for word in reversed(s.text.split(' ')):
                                if (
                                        word.split(':')[0] == 'http' or
                                        word.split(':')[0] == 'https'
                                ):
                                        tfield.insert(counter, " ")
                                        tfield.insert(counter,
                                                    word,
                                                    linkman.add(clickLink,
                                                              word,
                                                              "hyper"))
                                elif word.split('@')[0] == '':
                                        tfield.insert(counter,
                                                    word + " ",
                                                    linkman.add(clickAuthor,
                                                              word,
                                                              "inlineH"))
                                elif word.split('#')[0] == '':
                                        tfield.insert(counter,
                                                    word + " ",
                                                    linkman.add(hashThreader,
                                                              word,
                                                              "hash"))
                                elif word.find("&amp;") != -1:
                                        tfield.insert(counter,
                                                    word.replace("&amp;",
                                                                 "&")
                                                    + " ")
                                elif word.find("&lt;") != -1:
                                        tfield.insert(counter,
                                                    word.replace("&lt;",
                                                                 "<")
                                                    + " ")
                                elif word.find("&gt;") != -1:
                                        tfield.insert(counter,
                                                    word.replace("&gt;",
                                                                 ">")
                                                    + " ")
                                else:
                                        tfield.insert(counter, word + " ")
                        
                        tfield.insert(counter,
                                    newStat,
                                    linkman.add(clickAuthor, newStat, "handle"))
                
                except TclError:
                        if CON is not None:
                                CON.placeText((getTime()
                                               + ERRORS_SIGS['tcl'],
                                               'ERR'))
                        else:
                                ERR.append((getTime()
                                            + ERRORS_SIGS['tcl'],
                                            'ERR'))
                                print(ERRORS_SIGS['tcl'])
        
        tfield.config(state=DISABLED)


# starts a thread that runs a one-shot update on statuses.
#  this method, like the postThread method, is mainly
#  so the GUI doesn't freeze up while the method runs
def oneShotUpdate(event=None):
        one_update = upThread(3, "update", 1)
        one_update.start()


# starts a thread to make the GetSearch method run in the
#  background
def hashThreader(tag):
        hasher = upThread(5, 'hash', tag)
        hasher.start()

# the function that gets called whenever a user clicks on
#  a hashtag in the main window
def clickHash(tag):
        if SEARCH is not None:
                if CON is not None:
                        CON.placeText(ERRORS_SIGS['search'])
                else:
                        ERR.append(getTime()
                                   + ERRORS_SIGS['search'])
        else:
                global SEARCH
                SEARCH = searchDialog(root, "Search")
                SEARCH.putText(api.GetSearch(term=tag))


# takes the clicked on user name and puts it in the
#  entry box, making it easier to reply to people
def clickAuthor(handle):
        try:
                handle = handle.split('<')[1].split('>')[0]
        except:
                handle = handle.split('@')[1].split(':')[0]
        entry.insert(INSERT, "@" + handle + " ")


# supplies the callback to open links in the default
#  web browser
def clickLink(link):
        webbrowser.open(link)


# shows the console toplevel widget
def showConsole(event=None):
        if CON is not None:
                CON.placeText((getTime() + ERRORS_SIGS['console'], 'ERR'))
        else:
                global CON
                CON = conDialog(root, "Console")


# posts the status updates
def post():
        toPost = entry.get()
        entry.delete(0, END)
        
        global LAST_ID
        LAST_ID['self'] = api.PostUpdate(toPost).id


# deletes the last tweet posted by the user
def deleteTweet(event=None):
        if LAST_ID['self'] != 0:
                api.DestroyStatus(LAST_ID['self'])
                if CON is not None:
                        CON.placeText(getTime()
                                      + "- Last tweet deleted")
                else:
                        ERR.append(getTime()
                                   + "- Last tweet deleted")
        else:
                if CON is not None:
                        CON.placeText((getTime()
                                       + "- Last tweet was not deleted",
                                       'ERR'))
                else:
                        ERR.append((getTime()
                                   + "- Last tweet was not deleted", 'ERR'))


# keeps track of the chacter count and updates the GUI label
def numbers(entry):
        while STREAM_UPDATE:
                global TEXT
                TEXT.set(140 - len(entry.get()))
                sleep(.1)


# just an easy method that makes it easier to get the
#  current local time in the correct format
def getTime():
        secs = None
        minut = None
        hour = None
        if localtime().tm_sec < 10:
                secs = "0" + str(localtime().tm_sec) + " "
        else:
                secs = str(localtime().tm_sec) + " "
                
        if localtime().tm_min < 10:
                minut = "0" + str(localtime().tm_min)
        else:
                minut = str(localtime().tm_min)
        
        if localtime().tm_hour < 10:
                hour = "0" + str(localtime().tm_hour)
        else:
                hour = str(localtime().tm_hour)
        
        return str(hour
                   + ":" + minut
                   + ":" + secs)


# quits the threads and destroys the widgets
def quit(thread):
        
        if CON is not None:
                CON.close()
        
        if SEARCH is not None:
                SEARCH.close()
        
        global STREAM_UPDATE
        STREAM_UPDATE = False
        
        thread.join()
        
        root.destroy()


# starts a thread to run the post function. (Made this just so the GUI
#   doesn't unattractivly freeze up)
def postThreader(event=None):
        post_thread = upThread(2, "post", 0)
        post_thread.start()


# starts a thread to run the delete tweet function. this is just here
#  to keep the GUI from freezing up
def delThreader(event=None):
        del_thread = upThread(4, "del", 0)
        del_thread.start()


# gets the newest updates, while trying to stay within the Twitter's API
#   rate limit. has two modes, 0 and 1. 1 is just a one time thing, while
#   0 drops into a loop that checks every minute for new updates. 0 is meant
#   for the update thread and nothing else, while 1 is meant for the update
#   button.
def update(shot, last_id):
        if shot != 1:
                for i in range(18):
                        sleep(5)
                        if not STREAM_UPDATE:
                                break
                while STREAM_UPDATE:
                        STATUSES = list()
                        try:
                                STATUSES = api.GetHomeTimeline(since_id=last_id
                                                               )
                                
                                if len(STATUSES) != 0:
                                        last_id = STATUSES[0].id
                                
                                if (
                                        len(STATUSES) > 0 and
                                        LAST_ID['tweet'] != last_id
                                ):
                                        global LAST_ID
                                        LAST_ID['tweet'] = last_id
                                        updateDisplay(STATUSES, text, hyper)
                                
                                for i in range(18):
                                        sleep(5)
                                        if not STREAM_UPDATE:
                                                break
                                                
                                if not STREAM_UPDATE:
                                        break
                        except twitter.TwitterError:
                                if CON is not None:
                                        CON.placeText((getTime()
                                                      + ERRORS_SIGS['twitter'],
                                                       'ERR'))
                                else:
                                        print(ERRORS_SIGS['twitter'])
                                        ERR.append((getTime()
                                                    + ERRORS_SIGS['twitter'],
                                                    'ERR'))
                                for i in range(18):
                                        sleep(5)
                                        if not STREAM_UPDATE:
                                                break
                                                
                                if not STREAM_UPDATE:
                                        break
                        except URLError:
                                if CON is not None:
                                        CON.placeText((getTime()
                                                       + ERRORS_SIGS['net'],
                                                       'ERR'))
                                else:
                                        print(ERRORS_SIGS['net'])
                                        ERR.append((getTime()
                                                    + ERRORS_SIGS['net'],
                                                    'ERR'))
                                for i in range(18):
                                        sleep(5)
                                        if not STREAM_UPDATE:
                                                break
                                                
                                if not STREAM_UPDATE:
                                        break
                        
        else:
                try:
                        STATUSES = ()
                        STATUSES = api.GetHomeTimeline(since_id=last_id)
                
                        if len(STATUSES) > 0:
                                global LAST_ID
                                LAST_ID['tweet'] = STATUSES[0].id
                                updateDisplay(STATUSES, text, hyper)
                except twitter.TwitterError:
                        if CON is not None:
                                CON.placeText((getTime()
                                              + ERRORS_SIGS['twitter'], 'ERR'))
                        else:
                                print(ERRORS_SIGS['twitter'])
                                ERR.append((getTime()
                                            + ERRORS_SIGS['twitter'], 'ERR'))
                except URLError:
                        if CON is not None:
                                CON.placeText((getTime()
                                              + ERRORS_SIGS['net'], 'ERR'))
                        else:
                                print(ERRORS_SIGS['net'])
                                ERR.append((getTime()
                                           + ERRORS_SIGS['net'], 'ERR'))

# creates the access_token secret and key variables
#  to use to get the api reference
ASS_KEY = None
ASS_SECRET = None

# OS checking code.
if system() == "Windows":
        if not path.exists(path.expanduser('~\AppData\\Roaming\\tcler.txt')):
                get_access_token.startLogin()
else:
        # this assumes that if you aren't on windows, then
        #  you are running some Unix based system (including
        #  OS X)
        if not path.exists(path.expanduser('~/.tcler')):
                get_access_token.startLogin()
        
# gets the user's creds and splits the key and secret up
try:
        if system() != 'Windows':
                red = open(path.expanduser('~/.tcler'), 'r').read().split('\n')
        else:
                red = open(path.expanduser('~\AppData\\Roaming\\tcler.txt'),
                           'r').read().split('\n')
except:
        ERR.append((getTime() + ERRORS_SIGS['login'], 'ERR'))
        red = ['nope', 'nothing']

ASS_KEY = red[0]
ASS_SECRET = red[1]

# get the API reference
api = twitter.Api(consumer_key='qJwaqOuIuvZKlxwF4izCw',
                  consumer_secret='53dJ9tHJ77tAE8ywZIEU60JYPyoRU9jY2v0d58nI8',
                  access_token_key=ASS_KEY,
                  access_token_secret=ASS_SECRET)

# no statuses either
STATUSES = None

# try and get the statuses, while catching either a network error
#  or a twitter error
try:
        oneShotUpdate()
except URLError:
        ERR.append((getTime() + ERRORS_SIGS['net'], 'ERR'))
except twitter.TwitterError:
        ERR.append((getTime() + ERRORS_SIGS['twitter'], 'ERR'))

# tries to start a thread that just constantly runs the update function
#  (see the update function docs for more info)
try:
        UPDATE_THREAD = upThread(0, "update", LAST_ID['tweet'])
        
        UPDATE_THREAD.start()
except:
        ERR.append((getTime() + ERRORS_SIGS['update'], 'ERR'))

#
# STARTS SETTING UP TK GUI STUFF
#
root = Tk()
root.wm_title("Python Tcler - Twitter Client")
root.wm_minsize(width=200, height=400)
root.bind("<Return>", postThreader)
root.bind("<Control-u>", oneShotUpdate)
root.bind("<Control-c>", showConsole)
root.bind("<Control-d>", delThreader)

global TEXT
TEXT = StringVar(root)

scroll = Scrollbar(root)
scroll.pack(side=RIGHT, fill=Y, expand=0)

text = Text(root, yscrollcommand=scroll.set)
text.config(state=DISABLED, wrap=WORD)
text.pack(fill=BOTH, expand=1)

hyper = HyperlinkManager(text)

post_button = Button(root, text="Post", command=postThreader)
post_button.pack(side=RIGHT, fill=BOTH, expand=0)

Label(root, textvariable=TEXT).pack(side=RIGHT)

entry = Entry(root)
entry.focus()
entry.pack(fill=X, expand=1, side=RIGHT)

scroll.config(command=text.yview)

menu = Menu(root)
menu.add_command(label="Update", command=oneShotUpdate)
menu.add_command(label="Console", command=showConsole)
menu.add_command(label="Delete last tweet", command=delThreader)
menu.add_command(label="Quit", command=lambda: quit(UPDATE_THREAD))
root.config(menu=menu)

#
# END OF TK GUI STUFF
#

# tries to start a thread that will keep the character count
#  see the docs on the numbers function
try:
        NUMBER_THREAD = upThread(1, "numbers", entry)
        NUMBER_THREAD.start()
except:
        ERR.append((getTime() + ERRORS_SIGS['numbers'], 'ERR'))

# if the local variable err is still None, then no errors
#  occured since start up, otherwise a message is printed
#  saying to check the log (which, when opened will be
#  populated with all of the error messages, or otherwise,
#  that will hopefully help the user find the problem)
if len(ERR) > 4:
        text.config(state=NORMAL)
        text.insert(1.0, ERRORS_SIGS['generic'])

ERR.append(getTime() + "- Main window started")

root.mainloop()
