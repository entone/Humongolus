import unittest
import datetime
import objects
from pymongo.connection import Connection
import logging
import humongolus as orm

conn = Connection()
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("humongolus")

orm.settings(logger=logger, db_connection=conn)

class Field(unittest.TestCase):

    def setUp(self):
        self.name = "Anne"
        self.genitalia = "inny"
        self.obj = objects.Female()
        self.job = objects.Job()
        self.location = objects.Location()
    
    def test_default(self):
        self.assertEqual(self.obj.genitalia, self.genitalia)

    def test_field_set(self):
        self.obj.name = self.name
        self.assertEqual(self.obj.name, self.name)
    
    def test_required(self):
        self.obj.name = None
        with self.assertRaises(orm.DocumentException) as cm:
            self.obj.save()
    
    def test_embedded_required(self):
        self.obj.name = ""
        job = self.job
        job.title = ""
        location = self.location
        location.city = ""
        job.locations.append(location)
        self.obj.jobs.append(job)
        self.obj.name = self.name
        with self.assertRaises(orm.DocumentException) as cm:
            self.obj.save()
    
    def test_char(self):
        self.obj.name = "Anne"
        self.assertEqual(self.obj.name, "Anne")

        self.obj.name = "A"
        self.assertEqual(self.obj._get("name")._error.__class__.__name__, "MinException")

        self.obj.name = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.assertEqual(self.obj._get("name")._error.__class__.__name__, "MaxException")        

    def test_integer(self):

        self.obj.age = 27
        self.assertEqual(self.obj.age, 27)

        self.obj.age = -10
        self.assertEqual(self.obj._get("age")._error.__class__.__name__, "MinException")

        self.obj.age = 3001
        self.assertEqual(self.obj._get("age")._error.__class__.__name__, "MaxException")
    
    def test_float(self):

        self.obj.height = 100
        self.assertEqual(self.obj.height, 100.0)

        self.obj.height = -10
        self.assertEqual(self.obj._get("height")._error.__class__.__name__, "MinException")

        self.obj.height = 99999999
        self.assertEqual(self.obj._get("height")._error.__class__.__name__, "MaxException")

    def test_autoincrement(self):
        last_val = conn["auto_increment"]["human"].find_one({"field":"human_id"}, fields={"val":True})
        last_val = last_val["val"] if last_val else 0
        self.obj.name = self.name
        _id = self.obj.save()
        obj = objects.Female(id=_id)
        new_val = last_val+1
        self.assertEqual(obj.human_id, new_val)
        n = "%s%s" % (self.name, new_val)
        obj.name = n
        obj.save()
        n_obj = objects.Female(id=_id)
        self.assertEqual(n_obj.human_id, new_val)
        self.assertEqual(n_obj.name, n)
    
    def test_dynamic_document(self):
        self.obj.name = self.name
        _id = self.obj.save()
        scion = objects.Scion()
        scion.any_owner = self.obj
        s_id = scion.save()
        n_scion = objects.Scion(id=s_id)
        p = n_scion._get("any_owner")()
        self.assertEqual(p._id, _id)
    
    def compare_date(self, date1, date2):
        #mongo doesn't support the same date precision as python, gotta chop off a few microseconds
        diff = date1-date2
        self.assertLess(diff.microseconds, 1000)

    def test_timestamp(self): 
        obj = objects.Scion()
        _id = obj.save()
        timestamp = obj.silly_date
        obj2 = objects.Scion(id=_id)
        self.compare_date(timestamp, obj2.silly_date)

    def test_date(self):
        now = datetime.datetime.utcnow()
        obj = objects.Scion()
        obj.year = now
        _id = obj.save()
        obj2 = objects.Scion(id=_id)
        self.compare_date(now, obj2.year)


    def test_document_id(self):
        self.obj.name = self.name
        h_id = self.obj.save()
        car = objects.Scion()
        car.owner = self.obj
        _id = car.save()
        car2 = objects.Scion(id=_id)
        human = car2._get("owner")()
        self.assertEqual(human._id, h_id)

    def tearDown(self):
        self.obj.__class__.__remove__()

class Find(unittest.TestCase):

    def setUp(self):
        self.ids = []
        self.genitalia = "inny"
        for i in xrange(5):
            obj = objects.Female()
            obj.name = "Anne%s" % i
            obj.save()
            self.ids.append(obj._id)
    
    def test_find(self):
        ids = []
        for obj in objects.Female.find().sort('_id'):
            ids.append(obj._id)
        
        self.assertEqual(ids, self.ids)
    
    def test_fields(self):
        for obj in objects.Female.find(as_dict=True, fields={"genitalia":True}):
            self.assertEqual(obj.get('name', None), None)
            self.assertEqual(obj.get('genitalia', None), self.genitalia)


    def tearDown(self):
        objects.Female.__remove__()


class Document(unittest.TestCase):

    def setUp(self):
        self.job = objects.Job()
        self.job.employer = "Nike"
        self.job.title = "Designer"
        self.loc = objects.Location()
        self.loc.city = "Portland"
        self.loc.state = "OR"
        
        self.obj = objects.Female()
        self.obj.name = "Anne"
        self.obj.age = 27
        self.obj.height = 65
        self.obj.weight = 120

        self.person = {
            "name":u"Anne", 
            "age":27, 
            "height":65.0, 
            "weight":120.0,
            "genitalia":u"inny", 
            "jobs":[
                {
                    "employer":u"Nike", 
                    "title":u"Designer", 
                    "locations":[
                        {
                            "city":u"Portland", 
                            "state":u"OR"
                        }
                    ]
                }
            ]
        }
    
    def test_json(self):
        self.job.locations.append(self.loc)
        self.obj.jobs.append(self.job)
        j = self.obj._json()
        del j["human_id"]
        self.assertEqual(j, self.person)

    def test_save(self):
        self.job.locations.append(self.loc)
        self.obj.jobs.append(self.job)
        _id = self.obj.save()
        obj = self.obj.__class__(id=_id)
        j = self.obj._json()
        del j["human_id"]
        self.assertEqual(j, self.person)

    def test_empty_relationship(self):
        _id = self.obj.save()
        obj2 = self.obj.__class__(id=_id)
        obj2.jobs.append(self.job)
        self.job.locations.append(self.loc)
        obj2.save()
        obj3 = self.obj.__class__(id=_id)
        j = obj3._json()
        del j["human_id"]
        self.assertEqual(j, self.person)
    
    def test_created(self): pass
    def test_modified(self): pass
    def test_active(self): pass

    def tearDown(self):
        self.obj.__class__.__remove__()

class Lazy(unittest.TestCase):

    def setUp(self):
        self.obj = objects.Female()
        self.obj.name = "Anne"
        self.obj.age = 27
        self.obj.height = 65
        self.obj.weight = 120
        self.human_id = self.obj.save()
        self.car_ids = []
        for i in xrange(3):
            car = objects.Car()
            car.owner = self.human_id
            car.make = "Toyota"
            car.model = "Camry"
            car.year = datetime.datetime(2010+i, 1, 1)
            self.car_ids.append(car.save())

    def test_lazy(self):
        human = objects.Female(id=self.human_id)
        ids = []
        for c in human.cars().sort('_id'):
            ids.append(c._id)
        
        self.assertEqual(self.car_ids, ids)

    def tearDown(self):
        self.obj.__class__.__remove__()
        #objects.Car.__remove__()