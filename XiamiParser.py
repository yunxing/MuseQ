#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import logging
from opener import Opener
from bs4 import BeautifulSoup
from itertools import izip


URL = "http://www.xiami.com"
url_pattern = { "song": "http://www.xiami.com/search/song?", 
                "album": "http://www.xiami.com/search/album?",
                "artist": "http://www.xiami.com/search/artist?"}

def url_open(category, name):
    p = {'key':name}
    url = url_pattern[category] + urllib.urlencode(p)
    print url
    return BeautifulSoup(Opener.Instance().open(url))

def find_song_link(soup):
    yield "song_url"
    for link in soup.find_all('td', "song_name"):
        link = link.find('a', target="_blank")
        yield (URL + link.get('href'))
        
# category = "song_name", "song_artist", "song_album"
def find_song_info(soup, category):
    yield category
    for link in soup.find_all('td', class_=category):
        link = link.find('a', target="_blank")
        link = link.get('title')
        yield link

class XiamiParser(object):
    @staticmethod
    def search_song(name):
        soup = url_open("song", name)
        song_name = find_song_info(soup, "song_name")
        song_artist = find_song_info(soup, "song_artist")
        song_album = find_song_info(soup, "song_album")
        song_url = find_song_link(soup)
        zipped = izip(song_name, song_artist, song_album)
        return izip(izip(zipped, song_url), song_url)

    @staticmethod
    def search_album(name):
        soup = url_open("album", name)
        title_lst = ["album_name"]
        url_lst = ["album_url"]
        artist_lst = ["singer_name"]
        for link in soup.find_all('div', class_='album_item100_block'):
            artist_lst.append(link.find('p', class_='name').find('a', class_='singer').get('title'))
            url_lst.append(URL + link.find('p', class_='name').find('a').get('href'))
            title_lst.append(link.find('p', class_='name').find('a').get('title'))
        return izip(izip(title_lst, artist_lst), url_lst)

    @staticmethod
    def search_artist(name):
        soup = url_open("artist", name)
        artist_lst = ["artist_name"]
        url_lst = ["artist_url"]
        for link in soup.find_all('div', class_='artist_item100_block'):
            url_lst.append(URL + link.find('p', class_='buddy').find('a').get('href'))
            artist_lst.append(link.find('p', class_='name').find('span').get_text())
        return izip(artist_lst, url_lst)
   
def main():
    name = 'kelly'
    print name
    for item in XiamiParser.search_artist(name):
        print item
    
    
    
if __name__ == "__main__":
    main()
