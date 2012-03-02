import sys
sys.path.insert(0, "../")

import humongolus as orm
import tornado.web
import tornado.template
import tornado.httpserver
import json
import objects
import logging
from pymongo.objectid import ObjectId
from pymongo.connection import Connection

class AppHandler(tornado.web.RequestHandler):

    def __init__(self, *args, **kwargs):
        super(AppHandler, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        obj = objects.BadHuman()
        form = objects.HumanForm(object=obj, action="/", id="test")
        

        for i in objects.BadHuman.find():
            obj2 = i
            break
        

        print obj2.location.address.street
        if obj2 is None: 
            print "empty"
            obj2  = objects.BadHuman()

        form2 = objects.HumanForm(object=obj2, prepend='initial', action="/", id="woot")

        return self.render("index.html", form2=form2, form=form)
       
    def post(self, *args, **kwargs):
        context = {"success":False, "data":None}
        try:
            submit = json.loads(self.get_argument("form", "{}"))
            print submit
        except Exception as e:
            print e
        else:
            obj = objects.BadHuman()
            form = objects.HumanForm(object=obj, action="/", id="test", data=submit)
            try:
                form.validate()
                id = obj.save()
                print id
            except orm.DocumentException as e:
                obj = {}
                for k,v in e.errors.iteritems():
                    obj[k] = v.message
                context['data'] = obj
                self.finish(json.dumps(context))
            else:
                context['success'] = True
                context['data'] = str(id)
                self.finish(json.dumps(context))

SERVER_SETTINGS = {
    "static_path": "/home/entone/dev/Humongolus/example",
}

ROUTES = [
    tornado.web.URLSpec(r"/?", AppHandler, name="App"),
]


TORNADO_APP = tornado.web.Application(ROUTES, **SERVER_SETTINGS)

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("humongolus")

orm.settings(logger=logger, db_connection=Connection())

class Server(object):
    def __init__(self, port):
        server = tornado.httpserver.HTTPServer(TORNADO_APP)
        server.bind(port)
        server.start()
        tornado.ioloop.IOLoop.instance().start()

server = Server(port=8888)