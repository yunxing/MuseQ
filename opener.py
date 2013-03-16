import urllib2
from core import *

opener = None

@Singleton
class Opener(object):
    def __init__(self):
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-agent', 'Mozilla/5.0'),
                                  ('Referer', 'http://www.xiami.com/')]
        return opener

    def open(self, url):
        return self.opener.open(url).read()

    def urlretrive(self, url, path, fn_progress=None, fn_finished=None):
        f = self.opener.open(url)
        total = int(f.info().getheader("Content-Length", "0"))
        BUFFER_SIZE = total / 100
        downloaded = 0
        with open(path, "wb") as f:
            for data in iter((lambda:f.read(BUFFER_SIZE)),''):
                f.write(f)
                downloaded += len(data)
                fn_progress and fn_progress(downloaded, total)
        fn_finished and fn_finished()
