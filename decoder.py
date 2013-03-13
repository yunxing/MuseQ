import math
import re
import urllib2
import sys
import urllib
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

def getRegex(song_id, opener, regex):
    url = "http://www.xiami.com/song/playlist/id/%s/object_name/default/object_id/0" % song_id
    regex = re.compile(regex, re.MULTILINE|re.DOTALL)
    content = opener.open(url).read()
    return  regex.match(content).group(1)

def getOpener():
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    return opener

if __name__ == "__main__":
    opener = getOpener()
    loc = getRegex(sys.argv[1], opener, r".*\<location\>(.*?)\</location\>.*")
    name = getRegex(sys.argv[1], opener, r".*title\>\<\!\[CDATA\[(.*?)\]\].*")
    print name
    print decodeLocation(loc)
