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

class Song(object):
    def get_name(self):
        return self.file_name

    def is_complete(self):
        return True

    def stop(self):
        pass

    def get_ready(self):
        pass

class SongOnDisk(Song):
    def __init__(self, file_name, fn_add):
        self.file_name = file_name
        self.fn_add = fn_add

    def start(self):
        self.fn_add(self.file_name)

class SongInProgress(Song):
    def __init__(self, url, file_path, file_name, fn_add):
        self.file_path = file_path
        self.file_name = file_name
        self.url = url
        self.fn_add = fn_add
        self.ready = False
        self.complete = False
        self.download_started = False
        self.should_start = False
        self.started = False

    def stop(self):
        logging.debug("stopping %s"%self.file_name)
        self.should_start = False

    def is_complete(self): return self.complete

    def complete_download(self) : self.complete = True

    def get_ready(self):
        if not self.download_started:
            self.download_started = True
            Opener.Instance().urlretrive(self.url, self.file_path,
                                         self.check_and_add)

    def start(self):
        logging.info("staring play %s", self.file_name)
        self.should_start = True
        self.get_ready()
        if self.ready and not self.started:
            self.started = True
            self.fn_add(self.file_name)

    def check_and_add(self, download, total):
        if self.ready: return
        if download > total * 0.6 or total > 1024 * 1024 and download > 500 * 1024:
            self.ready = True
            if self.should_start and not self.started:
                logging.debug("caching complete: %s"%self.file_name)
                self.started = True
                self.fn_add(self.file_name)

class Playlist(object):
    def __init__(self):
        self.client_status = mpd.MPDClient(use_unicode=True)
        self.client_status.connect("localhost", 6600)

        self.client_action = mpd.MPDClient(use_unicode=True)
        self.client_action.connect("localhost", 6600)

        self.check_start()
        #May or may not be thread safe, use it for prototype now
        self.playlist = []
        self.repeat = False
        self.current = 0
        self.is_playing = False

    @core.run_in_thread
    def check_start(self):
        while True:
            self.client_status.idle("player")
            if self.client_status.status()["state"] == "stop":
                self.play_next_song()

    def play_next_song(self):
        self.is_playing = False
        self.current += 1
        self.play()

    def play(self):
        if self.is_playing: return
        try:
            next_song = self.playlist[self.current]
        except IndexError:
            self.is_playing = False
            return
        self.is_playing = True
        self.play_threading(next_song)
    @core.run_in_thread
    def play_threading(self, song):
        song.start()

    def add_and_play(self, name):
        try:
            self.client_action.clear()
            if not self.client_action.find("any", name):
                self.client_action.update()
            while not self.client_action.find("any", name): time.sleep(0.5)
            assert self.client_action.status()["state"] == "stop"
            self.client_action.add(name)
            self.client_action.play()
        except Exception as e:
            logging.warning("reconnecting %s!"%e)
            self.client_action.connect("localhost", 6600)
            self.add_and_play(name)

    def next_song(self):
        if not self.is_playing:
            return
        self.playlist[self.current].stop()
        try:
            if self.client_action.status()["state"] != "stop":
                self.client_action.stop()
            else:
                logging.debug(
                    "current song %s is not playing, skip to next"%self.playlist[self.current].get_name())
                self.play_next_song()
        except Exception as e:
            logging.warning("reconnecting %s!"%e)
            self.client_action.connect("localhost", 6600)
            self.next_song()

    def add_song(self, url, file_path, file_name):
        if not os.path.isfile(file_path):
            song = SongInProgress(url, file_path, file_name,
                                  self.add_and_play)
        else:
            song = SongOnDisk(file_name, self.add_and_play)
        self.playlist.append(song)
        self.play()

class MuseQ(object):
    def __init__(self, path, db_name, fn_progress=None, fn_complete=None):
        self.path = path
        self.db = MusicDB(path, db_name)
        self.fn_progress = fn_progress
        self.fn_complete = fn_complete
        self.playlist = Playlist()

    def play_single(self, url, name):
        file_name = name + "." + core.get_file_suffix(url)
        file_name = file_name.replace("/", "\\")
        file_path = self.path + "/" + file_name
        self.playlist.add_song(url, file_path, file_name)

    def play_streaming(self, url, name):
        raise Exception("not implemented")

    def next(self):
        self.playlist.next_song()

    def play(self, url):
        decoded_urls = dispatch_url(url)
        print decoded_urls
        for (decoded_url, name, streaming) in decoded_urls:
            if streaming:
                self.play_streaming(decoded_url, name)
            else:
                self.play_single(decoded_url, name)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    machine = MuseQ(const.PATH, const.DB_NAME)
    machine.play(sys.argv[1])
