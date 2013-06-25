from distutils.core import setup
import py2exe
import sys

if len(sys.argv) == 1:
    sys.argv.append("py2exe")
    sys.argv.append("-q")

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.version = "0.9.5"
        self.company_name = ""
        self.copyright = "2013 theZacAttacks"
        self.name = "Python Tcler"

twitclient = Target(
    description = "A simple Twitter client written in Python",
    script = "twitclient.py",
    dest_base = "twitclient")

setup(
    options = {'py2exe': {'compressed': True}},
    zipfile = None,
    windows = [twitclient],
    )
