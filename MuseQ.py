import core
from opener import Opener
from MusicDB import MusicDB
from dispatcher import dispatch_url
#from functools import partial
import mpd
import eyed3
import time
import logging
import os
import config
import const
import sys
import itertools
import XiamiParser
from threading import Event, Thread
from core import run_in_thread

class Song(object):
    def __init__(self):
        self.started = False
        self.is_current = False
        self.ready = True
        self.is_pause = False
    def toggle(self):
        self.is_pause = not self.is_pause

    def get_is_pause():
        return self.is_pause

    def started_ready(self):
        return True

    def get_title(self):
        return self.title

    def get_album(self):
        return self.album

    def get_artist(self):
        return self.artist

    def __eq__(self, other):
        return self.file_path == other.file_path

    def get_file_path(self):
        return self.file_path

    def stop(self):
        logging.debug("stopping %s" % self.file_name)
        self.is_current = False
        self.started = False
        self.is_pause = False

    def get_ready(self):
        pass

    def play(self, player):
        if not self.ready:
            return
        if self.is_current and not self.started:
            self.started = True
        player.clear()
        if not player.find("any", self.file_name):
            player.update()
        while not player.find("any", self.file_name):
            time.sleep(0.5)
        assert player.status()["state"] == "stop"
        player.add(self.file_name)
        player.play()
        assert player.status()["state"] != "stop"
        while player.status()["state"] != "stop":
            player.idle("player")
        logging.debug("finished playing: %s" % self.file_name)

class SongOnDisk(Song):
    def __init__(self, file_path, file_name):
        Song.__init__(self)
        self.file_name = file_name
        self.file_path = file_path
        self.get_tag()

    def get_tag(self):
        audiofile = eyed3.load(self.file_path)
        if audiofile.tag:
            self.artist = audiofile.tag.artist
            self.album = audiofile.tag.album
            self.title = audiofile.tag.title
        else:
            self.title = self.file_name
            self.album = "unknown"
            self.artist = "unknown"

    def start(self, player):
        self.play(player)


class SongInProgress(Song):
    def __init__(self, url, file_path, file_name,
                 title, album, artist):
        Song.__init__(self)
        self.file_path = file_path
        self.file_name = file_name
        self.title = title
        self.album = album
        self.artist = artist
        self.url = url
        self.ready = False
        self.event_wait = Event()
        self.event_wait.clear()
        self.pause_event = Event()
        self.pause_event.set()
        self.download_started = False

    def stop(self):
        super(SongInProgress, self).stop()
        self.event_wait.set()
        self.pause_event.set()

    def toggle(self):
        super(SongInProgress, self).toggle()
        if self.pause_event.is_set():
            self.pause_event.clear()
        else:
            self.pause_event.set()

    def write_tag(self):
        audiofile = eyed3.load(self.file_path)
        if not audiofile.tag:
            audiofile.tag = eyed3.id3.tag.Tag()
            audiofile.tag.artist = self.artist
            audiofile.tag.album = self.album
            audiofile.tag.title = self.title
            audiofile.tag.save(self.file_path)

    def started_ready(self):
        return self.download_started

    def get_ready(self):
        if not self.download_started:
            self.download_started = True
            try:
                progress = Opener.Instance().urlretrive(self.url, self.file_path)
                for (download, total) in progress:
                    self.check_and_play(download, total)
                logging.info("download complete: %s" % self.file_name)
                self.write_tag()
            except:
                self.ready = False
                self.event_wait.clear()
                self.download_started = False
                os.unlink(self.file_path)

    def start(self, player):
        logging.info("starting play %s",
                     self.file_name)
        self.is_current = True
        # dispatch a worker to download
        run_in_thread(self.get_ready)
        if not self.ready:
            logging.debug("started waiting...")
            self.event_wait.wait()
            logging.debug("finished waiting...")
        self.pause_event.wait()
        self.play(player)

    def check_and_play(self, download, total):
        if download > total * 0.6 or total > 1024 * 1024 and download > 1024 * 1024:
            self.ready = True
            self.event_wait.set()

class Proactive_downloader(object):
    def __init__(self, playlist):
        self.playlist = playlist
        self.download_id = 0
        self.event_stop = Event()
        self.event_stop.clear()

    def playlist_changed(self):
        self.event_stop.set()

    def playstatus_changed(self):
        # don't care
        pass

    def start(self):
        while True:
            logging.debug("downloader sleep")
            self.event_stop.wait()
            logging.debug("downloader wakeup")
            if self.playlist.is_empty():
                self.event_stop.clear()
                continue

            if all(x.started_ready() for x in self.playlist.playlist):
                self.event_stop.clear()
                continue

            start_id = self.playlist.change_id(self.playlist.current + 1)
            chained_list = itertools.chain(self.playlist.playlist[start_id:],
                                           self.playlist.playlist[:start_id])
            logging.debug("start proactively downloading")
            for song in chained_list:
                if song.started_ready():
                    continue
                logging.info("proactively downloading song %s " % song)
                # Start a worker to download, then wait for finish
                t = run_in_thread(song.get_ready)
                t.join()

class Playlist(object):
    def __init__(self):
        self.player = mpd.MPDClient(use_unicode=True)
        self.player.connect("localhost", 6600)

        self.client_action = mpd.MPDClient(use_unicode=True)
        self.client_action.connect("localhost", 6600)
        self.client_action.clear()

        #May or may not be thread safe, use it for prototype now
        self.playlist = []
        self.current = 0
        self.is_playing = Event()
        self.observers = set([])

    def is_empty(self):
        return self.playlist == []

    def get_current_song(self):
        return self.playlist[self.current]

    def playlist_changed(self):
        for obj in self.observers:
            obj.playlist_changed()

    def playstatus_changed(self):
        for obj in self.observers:
            obj.playstatus_changed()

    def change_id(self, id):
        if self.playlist:
            return id % len(self.playlist)
        else:
            return 0

    def change_current(self, new_current):
        self.current = self.change_id(new_current)

    def start(self):
        while True:
            self.is_playing.wait()
            current = self.current
            logging.debug("before play: current %d and self.current %d" % (current,
                                                                     self.current))
            song = self.get_current_song()
            song.start(self.player)
            logging.debug("after play: current %d and self.current %d" % (current,
                                                              self.current))
            if current == self.current:
                self.change_current(self.current + 1)
            self.playlist_changed()

    def to_list(self):
        return [{"id": i,
                 "title": song.get_title(),
                 "album": song.get_album(),
                 "artist": song.get_artist(),
                 "playing": i == self.current}
                for (i, song) in enumerate(self.playlist)
                ]

    def playstatus(self):
        try:
            return "pause" if self.get_current_song().is_pause else "play"
        except:
            return "stop"

    def add_song(self, url, file_path, file_name,
                 title, album, artist):
        if len(filter(lambda x:x.file_path == file_path, self.playlist)):
            return
        if not os.path.isfile(file_path):
            song = SongInProgress(url, file_path, file_name, title,
                                  album, artist)
        else:
            song = SongOnDisk(file_path, file_name)
        self.playlist.append(song)
        self.is_playing.set()
        self.playstatus_changed()

    def stop(self):
        self.playlist = []
        self.playlist_changed()
        self.is_playing.clear()
        self.client_action.stop()
        self.curren = 0
        self.playstatus_changed()

    def next_song(self):
        self.get_current_song().stop()
        self.client_action.stop()
        self.playstatus_changed()

    def set_volum(self, vol):
        if vol >= 100:
            vol = 100
        if vol <= 0:
            vol = 0
        self.client_action.setvol(vol)

    def volumeup(self):
        vol = self.client_action.status()["volume"]
        self.set_volum(int(vol) + 10)

    def volumedown(self):
        vol = self.client_action.status()["volume"]
        self.set_volum(int(vol) - 10)

    def select(self, id):
        if id >= len(self.playlist):
            return
        if self.current == id:
            return
        logging.info("jumping to song id %d" % id)
        self.get_current_song().stop()
        self.current = id
        self.client_action.stop()
        self.playstatus_changed()

    def toggle(self):
        try:
            self.get_current_song().toggle()
        except IndexError:
            pass

        if self.client_action.status()["state"] == "pause":
            self.client_action.play()
        elif self.client_action.status()["state"] == "play":
            self.client_action.pause()
        self.playstatus_changed()

class MuseQ(object):
    def __init__(self, path):
        self.path = path
        self.playlist = Playlist()
        self.downloader = Proactive_downloader(self.playlist)
        self.playlist.observers.add(self.downloader)

    def get_playlist(self):
        return self.playlist.to_list()

    def get_playstatus(self):
        return self.playlist.playstatus()

    def start(self):
        run_in_thread(self.playlist.start)
        run_in_thread(self.downloader.start)


    def register_updates(self, obj):
        self.playlist.observers.add(obj)
        obj.playlist_changed()
        obj.playstatus_changed()

    def deregister_updates(self, obj):
        self.playlist.observers.remove(obj)

    def play_single(self, url, id, title, album, artist):
        file_name = id + "." + core.get_file_suffix(url)
        file_path = self.path + "/" + file_name
        self.playlist.add_song(url, file_path, file_name,
                               title, album, artist)

    def play_streaming(self, url, name):
        raise Exception("not implemented")

    def next(self):
        self.playlist.next_song()

    def stop(self):
        self.playlist.stop()

    def volumeup(self):
        self.playlist.volumeup()

    def volumedown(self):
        self.playlist.volumedown()

    def toggle(self):
        self.playlist.toggle()

    def select(self, id):
        self.playlist.select(id)

    def search(self, query, cb):
        ret = {}
        def f1(): ret["songs"] = list(XiamiParser.search_song(query))
        def f2(): ret["albums"] = list(XiamiParser.search_album(query))
        t1 = core.run_in_thread(f1)
        t2 = core.run_in_thread(f2)
        t1.join()
        t2.join()
        cb(ret)

    def play(self, url):
        decoded_urls = dispatch_url(url)
        for (decoded_url, id, title, album, artist,
             streaming) in decoded_urls:
            if streaming:
                self.play_streaming(decoded_url, name)
            else:
                self.play_single(decoded_url, id, title,
                                 album, artist)
        self.playlist.playlist_changed()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    machine = MuseQ(const.PATH, const.DB_NAME)
    machine.play(sys.argv[1])
