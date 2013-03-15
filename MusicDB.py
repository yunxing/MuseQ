import cPickle as pickle

class MusicDB(object):
    def __init__(self, path, db_name):
        try:
            self.songs = pickle.load(open(
                    path + "/" + db_name, "rb" ))
        except:
            self.songs = {}
        self.path = path

    def add_song(self, raw_name, song_name):
        self.songs[raw_name] = song_name

    def get_song(self, raw_name):
        try:
            song_name = self.songs[raw_name]
            return song_name
        except KeyError:
            return None

if __name__ == "__main__":
    import tempfile
    tmp = tempfile.gettempdir()
    db = MusicDB(tmp, "music.p")
    key = "http://f1.xiami.net/23375/506629/01_1770937432_3197909.mp3"
    value = "hi.mp3"
    db.add_song(key, value)
    assert(db.get_song(key) == value)
    db.close()
