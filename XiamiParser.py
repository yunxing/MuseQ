import urllib2
from opener import Opener
import urllib
from bs4 import BeautifulSoup

url_pattern = "http://www.xiami.com/search?key="

class XiamiParser(object):
    def __init__(self, name):
        p = {'wd':name}
        url = url_pattern + urllib.urlencode(p)
        self.content = Opener.Instance().open(url)
        self.soup = BeautifulSoup(self.content)
        self.head_info = ('song_name', 'song_artist', 'song_album')
        self.song_name = []
        self.song_artist = []
        self.song_album = []
        self.song_link = []
        self.song_tuple = []

    def search_all(self):
        self.find_song_name()
        self.find_song_artist()
        self.find_song_album()
        self.find_song_link()
        for i in xrange(len(self.song_name)):
            self.song_tuple.append(((self.song_name[i], self.song_artist[i], self.song_album[i]), self.song_link[i]))
            print self.song_tuple[i]
        return self.song_tuple

    def find_song_name(self):
        for item in self.find_song_info("song_name"):
            self.song_name.append(item)

    def find_song_artist(self):
        for item in  self.find_song_info("song_artist"):
            self.song_artist.append(item)

    def find_song_album(self):
        for item in self.find_song_info("song_album"):
            self.song_album.append(item)

    def find_song_link(self):
        for link in self.soup.find_all('td', "song_name"):
            link = link.find('a', target="_blank")
            link = "http://wwww.xiami.com" + link.get('href')
            self.song_link.append(link)
        
    # category = "song_name", "song_artist", "song_album"
    def find_song_info(self, category):
        for link in self.soup.find_all('td', class_=category):
            link = link.find('a', target="_blank")
            link = link.get('title')
            yield link

def main():
    name = '十年'
    a = XiamiParser(name)
    a.search_all()

    
if __name__ == "__main__":
    main()
