import tornado.web
import tornado.ioloop
from api.config import Config
from api.ping_handler import PingHandler


class Application(tornado.web.Application):

    def __init__(self, config):
        self.config = config
        handlers = [(r"/ping", PingHandler)]
        settings = {}

        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    config = Config()
    app = Application(config)

    app.listen(8000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
