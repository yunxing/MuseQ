__author__ = 'yunxing'


class Playlist(object):

    def __init__(self):
        """
        A playlist class to support song changes

        """
        self.list = []
        self.current = 0

    def get_current_song(self):
        """
        :return:
         None if the playlist doesn't have a song.
         Otherwise, return current song.
        """
        if not self.list:
            return None
        try:
            return self.list[self.current]
        except IndexError:
            assert False

            



