import urllib2
import logging
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

    @run_in_thread
    def urlretrive(self, url, path, fn_progress=None, fn_finished=None):
        logging.info("started downloading %s " % url)
        f = self.opener.open(url)
        total = int(f.info().getheader("Content-Length", "0"))
        BUFFER_SIZE = total / 10
        if BUFFER_SIZE == 0: BUFFER_SIZE = 1024
        downloaded = 0
        with open(path, "wb", 0) as out:
            for data in iter((lambda:f.read(BUFFER_SIZE)),''):
                out.write(data)
                downloaded += len(data)
                fn_progress and fn_progress(downloaded, total)
        logging.info("finished downloading %s" % url)
        fn_finished and fn_finished()
