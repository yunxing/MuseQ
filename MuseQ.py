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

logging.basicConfig(level=logging.DEBUG)

class SongInProgress(object):
    def __init__(self, url, file_path, file_name, fn_add):
        self.file_path = file_path
        self.file_name = file_name
        self.url = url
        self.fn_add = fn_add
        self.added = False

    def start(self):
        Opener.Instance().urlretrive(self.url, self.file_path,
                                     self.check_and_add)

    def check_and_add(self, download, total):
        if self.added: return
        if download > total * 0.5 or download > 1024 * 1024 and download > total * 0.05:
            self.added = True
            self.fn_add(self.file_name, self.file_path)

class MuseQ(object):
    def __init__(self, path, db_name, fn_progress=None, fn_complete=None):
        self.path = path
        self.db = MusicDB(path, db_name)
        self.fn_progress = fn_progress
        self.fn_complete = fn_complete
        self.mpc = mpd.MPDClient(use_unicode=True)
        self.mpc.connect("localhost", 6600)

    def add_and_play(self, name, path):
        if not self.mpc.find("any", name):
            self.mpc.update()
        while not self.mpc.find("any", name): time.sleep(0.5)
        self.mpc.add(name)
        self.mpc.play()

    def play_single(self, url, name):
        file_name = name + "." + core.get_file_suffix(url)
        file_path = self.path + "/" + file_name
        #file is not downloaded, download it
        if not os.path.isfile(file_path):
            song = SongInProgress(url, file_path, file_name, self.add_and_play)
            song.start()
        else:
            self.add_and_play(file_name, file_path)

    def play_streaming(self, url, name):
        raise Exception("not implemented")

    def play(self, url):
        decoded_urls = dispatch_url(url)
        for (decoded_url, name, streaming) in decoded_urls:
            if streaming:
                self.play_streaming(decoded_url, name)
            else:
                self.play_single(decoded_url, name)

if __name__ == "__main__":
    machine = MuseQ(const.PATH, const.DB_NAME)
    machine.play(sys.argv[1])
