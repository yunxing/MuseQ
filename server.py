import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import core
import const
from MuseQ import MuseQ

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/ws", SocketHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class SocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    machine = MuseQ(const.PATH, const.DB_NAME)

    def allow_draft76(self):
        # for iOS 5.0 Safari
        return True

    def open(self):
        SocketHandler.waiters.add(self)

    def on_close(self):
        SocketHandler.waiters.remove(self)

    def on_message(self, message):
        logging.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        if parsed["command"] == "addurl":
            SocketHandler.machine.play(parsed["url"])
        elif parsed["command"] == "next":
            SocketHandler.machine.next()

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
