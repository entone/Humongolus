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
        
        form = objects.SimpleForm(action="/", id="test")

        form2 = objects.HumanForm(action="/")
        
        return self.render("index.html", form=form, form2=form2)
       
    def post(self, *args, **kwargs):
        context = {"success":False, "data":None, "html":None}
        try:
            submit = json.loads(self.get_argument("form", "{}"))
            print submit
        except Exception as e:
            print e
        else:
            obj = objects.BadHuman()
            form = objects.SimpleForm(object=obj, action="/", id="test", data=submit)
            try:
                form.validate()
                id = obj.save()
                context['data'] = str(id)
                context['success'] = True
            except orm.DocumentException as e:
                context['success'] = False
                obj = {}
                for k,v in e.errors.iteritems():
                    obj[k] = v.message
                context['data'] = obj
            finally:
                context['html'] = self.render_string("form.html", form=form)
                print context
                self.finish(json.dumps(context))

SERVER_SETTINGS = {
    "static_path": "/home/entone/Humongolus/example",
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