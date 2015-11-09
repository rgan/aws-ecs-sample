from tornado.web import RequestHandler


class PingHandler(RequestHandler):

    def get(self):
        self.write(self.application.config["message"])