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

define("port", default=8080, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/ws", SocketHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            # debug=True,
            )
        tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class SocketHandler(tornado.websocket.WebSocketHandler):
    machine = MuseQ(const.PATH)
    machine.start()

    def playlist_changed(self):
        playlist = SocketHandler.machine.get_playlist()
        msg = {}
        msg["command"] = "update"
        msg["arg"] = playlist
        try:
            self.write_message(msg)
        except:
            logging.error("Error sending message", exc_info=True)

    def playstatus_changed(self):
        status = SocketHandler.machine.get_playstatus()
        msg = {}
        msg["command"] = "toggle"
        msg["arg"] = status
        try:
            self.write_message(msg)
        except:
            logging.error("Error sending message", exc_info=True)

    def query_result_got(self, result):
        msg = {}
        msg["command"] = "result"
        msg["arg"] = result
        try:
            self.write_message(msg)
        except:
            logging.error("Error sending message", exc_info=True)

    def allow_draft76(self):
        return True

    def open(self):
        SocketHandler.machine.register_updates(self)
        self.playlist_changed()
        self.playstatus_changed()

    def on_close(self):
        SocketHandler.machine.deregister_updates(self)

    def on_message(self, message):
        logging.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        if parsed["command"] == "addurl":
            SocketHandler.machine.play(parsed["url"])
        elif parsed["command"] == "select":
            SocketHandler.machine.select(int(parsed["id"]))
        elif parsed["command"] == "next":
            SocketHandler.machine.next()
        elif parsed["command"] == "stop":
            SocketHandler.machine.stop()
        elif parsed["command"] == "volumeup":
            SocketHandler.machine.volumeup()
        elif parsed["command"] == "volumedown":
            SocketHandler.machine.volumedown()
        elif parsed["command"] == "toggle":
            SocketHandler.machine.toggle()
        elif parsed["command"] == "search":
            SocketHandler.machine.search(parsed["query"],
                                         self.query_result_got)

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
