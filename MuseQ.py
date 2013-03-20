import core
from opener import Opener
from MusicDB import MusicDB
from dispatcher import dispatch_url
#from functools import partial
import mpd
import time
import logging
import os
import core
import const
import config
import sys
from threading import Event
from wait_signaler import WaitSignaler

class Song(object):
    def __init__(self):
        self.started = False
        self.is_current = False
        self.ready = True

    def get_name(self):
        return self.file_name

    def stop(self):
        logging.debug("stopping %s"%self.file_name)
        self.is_current = False
        self.started = False

    def get_ready(self):
        pass

    def play(self, player):
        if not self.ready: return
        if self.is_current and not self.started:
            self.started = True
        player.clear()
        if not player.find("any", self.file_name):
            player.update()
        while not player.find("any", self.file_name): time.sleep(0.5)
        assert player.status()["state"] == "stop"
        player.add(self.get_name())
        player.play()
        assert player.status()["state"] != "stop"
        while player.status()["state"] != "stop":
            player.idle("player")

class SongOnDisk(Song):
    def __init__(self, file_name):
        Song.__init__(self)
        self.file_name = file_name

    def start(self, player):
        self.play(player)

class SongInProgress(Song):
    def __init__(self, url, file_path, file_name):
        Song.__init__(self)
        self.file_path = file_path
        self.file_name = file_name
        self.url = url
        self.ready = False
        self.event_wait = Event()

    def stop(self):
        super(SongInProgress, self).stop()
        self.event_wait.set()

    @core.run_in_thread
    def get_ready(self):
        if not self.download_started:
            self.download_started = True
            progress = Opener.Instance().urlretrive(self.url, self.file_path)
            for (download, total) in progress:
                self.check_and_play(download, total)

    def start(self, player):
        logging.info("starting play %s",
                     self.file_name)
        self.is_current = True
        self.get_ready()
        if not self.ready:
            self.event_wait.clear()
        self.play(player)

    def check_and_play(self, download, total):
        if download > total * 0.6 or total > 1024 * 1024 and download > 500 * 1024:
            self.ready = True
            self.event_wait.set()
            logging.debug("caching complete: %s"%self.file_name)
            self.play(player)

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

    def get_current_song(self):
        return self.playlist[self.current]

    def playlist_changed(self):
        for fn in self.observers:
            fn()

    def change_current(self, new_current):
        self.current = new_current
        if self.playlist:
            self.current = self.current % len(self.playlist)
        else:
            self.current = 0

    @core.run_in_thread
    def start(self):
        while True:
            self.is_playing.wait()
            current = self.current
            song = self.get_current_song()
            song.start(self.player)
            if current == self.current:
                self.change_current(self.current + 1)
            self.playlist_changed()

    def to_list(self):
        return [{"id":i,
                 "name":song.get_name(),
                 "playing":i==self.current}
                for (i, song) in enumerate(self.playlist)
                ]

    def add_song(self, url, file_path, file_name):
        if not os.path.isfile(file_path):
            song = SongInProgress(url, file_path, file_name)
        else:
            song = SongOnDisk(file_name)
        self.playlist.append(song)
        self.is_playing.set()

    def stop(self):
        self.playlist = []
        self.playlist_changed()
        self.is_playing.clear()
        self.client_action.stop()
        self.curren = 0

    def next_song(self):
        self.get_current_song().stop()
        self.client_action.stop()

class MuseQ(object):
    def __init__(self, path, db_name, fn_progress=None, fn_complete=None):
        self.path = path
        self.db = MusicDB(path, db_name)
        self.fn_progress = fn_progress
        self.fn_complete = fn_complete
        self.playlist = Playlist()

    def get_playlist(self):
        return self.playlist.to_list()

    def start(self):
        self.playlist.start()

    def register_updates(self, fn):
        self.playlist.observers.add(fn)

    def deregister_updates(self, fn):
        self.playlist.observers.remove(fn)

    def play_single(self, url, name):
        file_name = name + "." + core.get_file_suffix(url)
        file_name = file_name.replace("/", "\\")
        file_path = self.path + "/" + file_name
        self.playlist.add_song(url, file_path, file_name)

    def play_streaming(self, url, name):
        raise Exception("not implemented")

    def next(self):
        self.playlist.next_song()

    def stop(self):
        self.playlist.stop()

    def play(self, url):
        decoded_urls = dispatch_url(url)
        print decoded_urls
        for (decoded_url, name, streaming) in decoded_urls:
            if streaming:
                self.play_streaming(decoded_url, name)
            else:
                self.play_single(decoded_url, name)
        self.playlist.playlist_changed()



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    machine = MuseQ(const.PATH, const.DB_NAME)
    machine.play(sys.argv[1])
