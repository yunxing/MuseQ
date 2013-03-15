import math
import json
import re
import sys
import urllib
from opener import Opener

def substr(string, start, length):
    return string[start:start+length]

def decodeLocation(loc):
    v10 = 0
    v2 = int(loc[0])
    v3 = loc[1:]
    v4 = int(math.floor((len(v3) / v2)))
    v5 = (len(v3) % v2)
    v6 = []
    v7 = 0
    while v7 < v5:
        v6.append(substr(v3,(v4 + 1)*v7,v4+1))
        v7 = v7 + 1
    v7 = v5
    while v7 < v2:
        v6.append(substr(v3, v4*(v7-v5)+(v4+1)*v5, v4))
        v7 = v7 + 1
    v8 = ""
    v7 = 0
    try:
        while v7 < len(v6[0]):
            v10 = 0
            while v10 < len(v6):
                v8 = v8 + v6[v10][v7]
                v10 = v10 + 1
            v7 = v7 + 1
    except:
        pass
    v8 = urllib.unquote(v8)
    v9 = ""
    v7 = 0
    while v7 < len(v8):
        if v8[v7] == "^":
            v9 = v9 + "0"
        else:
            v9 = v9 + v8[v7]
        v7 = v7 + 1
    v9 = v9.replace("+", " ")
    return v9

def getSong(song_id):
    url = xiami_url["single_song"] % song_id
    content = Opener.Instance().open(url)
    encryptedLoc = getEncryptedLocation(content)
    return [decodeLocation(loc) for loc in encryptedLoc]

def getEncryptedLocation(content):
    return solveRegex(content, regexes["xiami"])

def solveRegex(content, pattern):
    return re.findall(pattern, content, re.MULTILINE|re.DOTALL)

regexes = {
    "xiami": r"<location\>(.*?)\</location\>"
    }

patterns = [
    (r".*xiami.com/song/(?P<song_id>.*)", getSong),
    ]

xiami_url = {
    "single_song": "http://www.xiami.com/song/playlist/id/%s/object_name/default/object_id/0"
    }

def dispatch_url(url, patterns):
    for (r, fn) in patterns:
        m = r.match(url)
        if m:
            return fn(m.group(1))
    raise Exception("unmatchable url")

if __name__ == "__main__":
    url = sys.argv[1]
    compiled = map(lambda (reg, fn): (re.compile(reg), fn), patterns)
    result = dispatch_url(url, compiled)
    print json.dumps(result)
