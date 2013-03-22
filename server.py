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
            debug=True,
            )
        tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class SocketHandler(tornado.websocket.WebSocketHandler):
    machine = MuseQ(const.PATH, const.DB_NAME)
    machine.start()

    def notify_playlist(self):
        playlist = SocketHandler.machine.get_playlist()
        msg = {}
        msg["command"] = "update"
        msg["arg"] = playlist
        try:
            self.write_message(msg)
        except:
            logging.error("Error sending message", exc_info=True)

    def allow_draft76(self):
        return True

    def open(self):
        SocketHandler.machine.register_updates(self.notify_playlist)
        self.notify_playlist()

    def on_close(self):
        SocketHandler.machine.deregister_updates(self.notify_playlist)

    def on_message(self, message):
        logging.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        if parsed["command"] == "addurl":
            SocketHandler.machine.play(parsed["url"])
        elif parsed["command"] == "next":
            SocketHandler.machine.next()
        elif parsed["command"] == "stop":
            SocketHandler.machine.stop()


def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
