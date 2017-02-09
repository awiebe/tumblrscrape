import sys
import os
from os import listdir



def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

dataDir = os.path.join(get_script_path(),"data")
onlyfiles = [f for f in listdir(dataDir) if os.path.isdir(os.path.join(dataDir, f)) ]
onlyfiles = filter(lambda (x): not os.path.basename(x).startswith("."),onlyfiles)

for f in onlyfiles:
    print "Updating..."+f
    sys.argv = ['tumblrScrape.py',f]
    execfile('tumblrScrape.py')