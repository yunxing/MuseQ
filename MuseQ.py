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
from threading import Event


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

    @core.run_in_thread
    def get_ready(self):
        if not self.download_started:
            self.download_started = True
            progress = Opener.Instance().urlretrive(self.url, self.file_path)
            for (download, total) in progress:
                self.check_and_play(download, total)
            logging.debug("download complete: %s" % self.file_name)
            self.write_tag()

    def start(self, player):
        logging.info("starting play %s",
                     self.file_name)
        self.is_current = True
        self.get_ready()
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
        for obj in self.observers:
            obj.playlist_changed()

    def playstatus_changed(self):
        for obj in self.observers:
            obj.playstatus_changed()

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
    def __init__(self, path, db_name, fn_progress=None, fn_complete=None):
        self.path = path
        self.db = MusicDB(path, db_name)
        self.fn_progress = fn_progress
        self.fn_complete = fn_complete
        self.playlist = Playlist()

    def get_playlist(self):
        return self.playlist.to_list()

    def get_playstatus(self):
        return self.playlist.playstatus()

    def start(self):
        self.playlist.start()

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
