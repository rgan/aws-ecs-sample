import json
from consul import base
import consul.tornado
import tornado.ioloop
import tornado.gen

class Config:

    def __init__(self):
        try:
            self.config = json.load(file("/etc/api/config.json"))
        except ValueError:
            raise Exception("Config file is not found or is not valid JSON")
        tornado.ioloop.IOLoop.instance().add_callback(self.watch)

    @tornado.gen.coroutine
    def watch(self):
        c = consul.tornado.Consul(host='dev')

        # asynchronously poll for updates
        index = None
        while True:
            try:
                index, data = yield c.kv.get('message', index=index)
            except base.Timeout:
                print "Timed out"
            if data:
                print "Received ..%s" % data['Value']
                self.config['message'] = data['Value']