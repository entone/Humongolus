import unittest
import datetime
import objects
from pymongo.connection import Connection
import logging
import humongolus as orm
from humongolus.field import FieldException

conn = Connection()
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("humongolus")

orm.settings(logger=logger, db_connection=conn)

class Widget(unittest.TestCase):

    def test_render(self):
        anne = objects.Female()
        anne.name = "Anne"
        print anne._get("name").render()

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
        car = objects.Scion()
        car.owner = self.obj
        with self.assertRaises(FieldException) as cm:
            car._get("owner")().name

        h_id = self.obj.save()
        car = objects.Scion()
        car.owner = self.obj
        _id = car.save()
        car2 = objects.Scion(id=_id)
        human = car2._get("owner")()
        self.assertEqual(human._id, h_id)
    

    def test_render(self):
        self.obj.name = self.name
        self.obj.age = 27
        self.assertEqual(self.obj._get("age").render(), 27)

    def test_geo(self):
        loc = objects.LocationGeo()
        print loc._json()
        loc.city = "Chicago"
        loc.state = "IL"

        loc.geo = "sdjfhskljdfhskdhf"
        self.assertEqual(loc._get("geo")._error.__class__.__name__, 'FieldException')
        print loc._get("geo")._error

        loc.geo = [545454, 654654, 654654]
        self.assertEqual(loc._get("geo")._error.__class__.__name__, 'FieldException')
        print loc._get("geo")._error

        loc.geo = [48.326, -81.656565]
        self.assertEqual(loc.geo, [48.326, -81.656565])

    def test_boolean(self):
        loc = objects.LocationGeo()
        print loc._json()
        loc.city = "Chicago"
        loc.state = "IL"
        loc.geo = [48.326, -81.656565]
        loc.active = "kjsdhfksjhdflksjhdflksjhdf"
        print loc.active
        self.assertEqual(loc.active, True)

        loc.active = 0
        self.assertEqual(loc.active, False)

        loc.active = True
        self.assertEqual(loc.active, True)
        
        loc.active = False
        self.assertEqual(loc.active, False)        
    
    def test_phone(self):
        obj = objects.BadHuman()
        print obj._get("phone")
        obj.name = "Anne"
        obj.phone = "sjkdhfkjshdfksjhdf"
        print obj._get("phone")
        self.assertEqual(obj._get("phone")._error.__class__.__name__, "FieldException")



        obj.phone = "810-542.0141"
        self.assertEqual(obj.phone, u"+18105420141")

        obj.phone = "1-810-542.0141"
        self.assertEqual(obj.phone, u"+18105420141")

    def test_email(self):
        obj = objects.BadHuman()
        obj.name = "Anne"
        obj.email = "sdsdff"
        self.assertEqual(obj._get("email")._error.__class__.__name__, "FieldException")

        obj.email = "test@trest"
        self.assertEqual(obj._get("email")._error.__class__.__name__, "FieldException")

        obj.email = "test@test.com"
        self.assertEqual(obj.email, "test@test.com")

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
        print self.ids
        for obj in objects.Female.find().sort('_id'):
            ids.append(obj._id)
        
        self.assertEqual(ids, self.ids)
    
    def test_fields(self):
        for obj in objects.Female.find(as_dict=True, fields={"genitalia":True}):
            self.assertEqual(obj.get('name', None), None)
            self.assertEqual(obj.get('genitalia', None), self.genitalia)

        obj = objects.Female.find_one({"_id":self.ids[0]}, as_dict=True, fields={"genitalia":True})
        self.assertEqual(obj.get("genitalia", None), self.genitalia)
    
    def test_update(self):
        obj = objects.Female(id=self.ids[0])
        obj.update({"$set":{"name":"Woop"}})
        obj2 = objects.Female(id=self.ids[0])
        self.assertEqual(obj2.name, "Woop")
    
    def test_remove(self):
        obj = objects.Female(id=self.ids[0])
        obj.remove()
        obj2 = objects.Female.find_one({"_id":self.ids[0]})
        self.assertEqual(obj2, None)

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
        _id = self.obj.save()
        o = self.obj.json()
        self.assertEqual(_id, o['_id'])
    
    def test_map(self):
        anne = objects.Female()
        anne._map(self.person)
        j = anne._json()
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
    
    def test_bad_rel_type(self):
        with self.assertRaises(Exception) as cm:
            self.obj.jobs.append(objects.Location())

        print cm.exception
    
    def test_bad_get(self):
        with self.assertRaises(AttributeError):
            self.obj._get("hoohaa")
    
    def test_bad_attr(self):
        with self.assertRaises(AttributeError):
            self.obj.hoohaa


    def test_non_doc_relationship(self):
        car = objects.Rodeo()
        car.tires.append(1)
        car.tires.append(2)
        car.tires.append(3)
        car.tires.append(4)
        _id = car.save()
        car2 = objects.Rodeo(id=_id)
        self.assertEqual(car2.tires, [1,2,3,4])
    
    def test_mongo_exception(self):
        obj = objects.BadHuman()
        obj._coll.ensure_index("name", unique=True)
        obj.name = "Test"
        obj.save()
        
        obj2 = objects.BadHuman()
        obj2.name = "Test"
        _id = obj2.save()
        self.assertEqual(_id, False)

        obj3 = objects.BadHuman()
        obj3.name = "Test"
        obj3.save()

        obj4 = objects.BadHuman()
        obj4.name = "Tester"
        obj4.save()
        obj4.name = "Test"
        _id2 = obj4.save()
        self.assertEqual(_id2, False)
        obj._coll.drop_indexes()
        

    def test_created(self):
        self.obj.save()
        print self.obj.created
        self.assertEqual(self.obj.created.__class__, datetime.datetime) 

    def test_modified(self):
        self.obj.save()
        print self.obj.modified
        self.assertEqual(self.obj.modified.__class__, datetime.datetime)

    def test_active(self):
        self.obj.save()
        self.assertEqual(self.obj.active, True)

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