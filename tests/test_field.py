import sys
if sys.version_info < (2,7):
    import unittest2 as unittest
else:
    import unittest
import datetime
import objects
import os
from pymongo.connection import Connection
import logging
import humongolus as orm
import humongolus.widget as widget
from humongolus.field import FieldException

conn = Connection()
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger("humongolus")

orm.settings(logger=logger, db_connection=conn)

class Field(unittest.TestCase):

    def setUp(self):
        self.name = "Anne"
        self.genitalia = "inny"
        self.obj = objects.Female()
        self.job = objects.Job()
        self.loca = objects.LocationGeo()
        self.location = objects.Location()

    def test_validation(self):
        obj = objects.BadHuman()
        obj.state = "Illinois"
        with self.assertRaises(orm.DocumentException) as cm:
            obj.save()

        obj.country = "USA"
        obj.state = "Illinois"

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
        try:
            obj.save()
        except Exception as e:
            print e
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
        car3 = objects.Scion()
        car3.any_owner = objects.Female()
        with self.assertRaises(orm.DocumentException) as cm:
            car3.save()
            print cm.exception.errors

        with self.assertRaises(Exception) as cm:
            car3._get("any_owner")()


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

    def test_choice(self):
        car = objects.Scion()
        car.color = "Red"

    def test_bad_choice(self):
        car = objects.Scion()
        car.color = "Invalid"
        with self.assertRaises(orm.DocumentException) as cm:
            car.save()

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
        car3 = objects.Scion()
        car3.owner = objects.Female()
        with self.assertRaises(orm.DocumentException) as cm:
            car3.save()
            print cm.exception.errors

    def test_geo(self):
        loc = objects.LocationGeo()
        loc.city = "Chicago"
        loc.state = "IL"
        loc.geo = "sdjfhskljdfhskdhf"
        self.assertEqual(loc._get("geo")._error.__class__.__name__, 'FieldException')

        loc.geo = [545454, 654654, 654654]
        self.assertEqual(loc._get("geo")._error.__class__.__name__, 'FieldException')

        loc.geo = [48.326, -81.656565]
        self.assertEqual(loc.geo, [48.326, -81.656565])

    def test_boolean(self):
        loc = objects.LocationGeo()
        print loc.__class__
        loc.city = "Chicago"
        loc.state = "IL"
        loc.geo = [48.326, -81.656565]
        loc.active = "kjsdhfksjhdflksjhdflksjhdf"
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

    def test_file(self):
        obj = objects.BadHuman()
        obj.name = "Anne"
        path = os.path.dirname(__file__)
        print path
        obj.avatar = file("%s/%s" % (path, "penguin.jpg"))
        f_id = obj.avatar
        self.assertEqual(obj._get("avatar").exists(), True)
        _id = obj.save()
        o = objects.BadHuman(id=_id)
        self.assertEqual(o.avatar, f_id)
        print o._get("avatar")()
        print o._get("avatar").list()
        print o._get("avatar").delete()
        self.assertEqual(obj._get("avatar").exists(), False)
        obj2 = objects.BadHuman()
        with self.assertRaises(FieldException) as cm:
            obj2._get("avatar")()

        obj2.name = "Anne"
        obj2.avatar = objects.BadHuman()
        with self.assertRaises(orm.DocumentException) as cm:
            obj2.save()
            print cm.exception.errors


    def tearDown(self):
        self.obj.__class__.__remove__()

class Find(unittest.TestCase):

    def setUp(self):
        self.ids = []
        self.genitalia = "inny"
        for i in xrange(5):
            obj = objects.Female()
            obj.name = "Anne%s" % i
            j = objects.Job()
            j.title = "President"
            obj.jobs.append(j)
            obj.save()
            self.ids.append(obj._id)

    def test_find(self):
        ids = []
        print self.ids
        for obj in objects.Female.find().sort('_id'):
            print obj.jobs[0]
            print obj.created
            print obj.json()
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



    def test_dbkey(self):
        obj = objects.BadHuman()
        obj.name = "Anne"
        obj.email = "test@test.com"
        _id = obj.save()
        dic = obj.find_one({"_id":_id}, as_dict=True)
        dic.get("em")

    def test_empty(self):
        obj = objects.BadHuman()
        with self.assertRaises(orm.DocumentException) as cm:
            obj.save()

    def test_repr(self):
        print unicode(self.obj)
        print self.obj
        print self.obj.jobs
        print unicode(self.obj.jobs)
        print self.obj.name
        print unicode(self.obj.name)
        print unicode(self.obj._get("name"))
        print orm.Widget(object=self.obj._get("name"), name="name").render()
        print unicode(self.obj.cars)

    def test_data_init(self):
        car = objects.Car(data={
            "make":"VW",
            "model":"Jetta",
            "year":datetime.datetime.utcnow(),
            "features": [u"leather", u"manual"],
        }, init=False)
        print "Data init: {}".format(car.json())
        print "Data init: {}".format(car.save())
        car2 = objects.Car(id=car._id)
        self.assertEqual(car.model, car2.model)


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

    def test_list_length(self):
        with self.assertRaises(Exception) as cm:
            for i in xrange(5):
                job = objects.Job()
                job.title = "Engineer %s" % i
                self.obj.jobs.append(job)

    def test_list_delete(self):
        person = self.obj
        self.job.locations.append(self.loc)
        person.jobs.append(self.job)
        person.save()
        id = person._id
        p2 = objects.Female(id=id)
        self.assertEqual(p2.jobs[0]._json(), self.person.get('jobs')[0])
        p2.jobs.delete('jobs', 0)
        p3 = objects.Female(id=id)
        self.assertEqual(len(p3.jobs), 0)

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
        with self.assertRaises(Exception) as cm:
            _id = obj2.save()

        obj.__class__.__remove__()
        obj3 = objects.BadHuman()
        obj3.name = "Test"
        obj3.save()

        obj4 = objects.BadHuman()
        obj4.name = "Tester"
        obj4.save()
        obj4.name = "Test"
        with self.assertRaises(Exception) as cm:
            _id2 = obj4.save()

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
        objects.Car.__remove__()

class SavingLoading(unittest.TestCase):

    def setUp(self):
        self.car = objects.Car()
        self.car.make = "Saab"
        self.car.model = "900"
        self.car.year = datetime.datetime(2007, 1, 1)

    def test_list_strings_0(self):
        self.car.features._map([u'CD-Player', u'Power Windows', u'Remote Start'])
        self.car.features.append(u"Test")
        try:
            self.car.save()
        except Exception as e:
            print e

        car = objects.Car(id=self.car._id)
        self.assertEqual(len(car.features), len(self.car.features))

    def test_list_strings_1(self):
        self.car.features.append(u'Test')
        self.car.features.append(u'AnotherTest')
        self.car.save()

        car = objects.Car(id=self.car._id)
        self.assertEqual(len(car.features), len(self.car.features))

        self.car.features.append(u'Yet again another')
        self.car.save()

        car = objects.Car(id=self.car._id)
        self.assertEqual(len(car.features), len(self.car.features))

        self.car.features.delete('features', 1)
        self.car.save()

        car = objects.Car(id=self.car._id)
        self.assertEqual(len(car.features), len(self.car.features))

    def test_lists_of_type(self):
        p0 = objects.Property()
        p0.name = "Type"
        p0.value = "Lumber"

        p1= objects.Property()
        p1.name = "Type"
        p1.value = "Camping gear"

        p2= objects.Property()
        p2.name = "Type"
        p2.value = "Sledgehammer"

        self.car.properties.append(p0)
        self.car.save()

        car = objects.Car.find_one(id=self.car._id)
        self.assertEqual(len(car.properties), len(self.car.properties))

        self.car.properties.append(p1)
        self.car.save()
        car = objects.Car.find_one(id=self.car._id)
        self.assertEqual(len(car.properties), len(self.car.properties))

        self.car.properties.delete('properties', 1)
        self.car.save()
        car = objects.Car(id=self.car._id)
        self.assertEqual(len(car.properties), len(self.car.properties))

    def test_add_new_field(self):
        self.car.save()

        class Hybrid(objects.Car):
            fuels = orm.List(type=objects.Property)

        hybrid_car = Hybrid(id=self.car._id)
        # This test will work if you call save upon loading (if new field was added)
        # Otherwise it will write the object as {'0': {'name': 'Ethanol', value: 'E85'}, '1': {.......}}
        #hybrid_car.save()

        p0 = objects.Property()
        p0.name = "Ethanol"
        p0.value = "E85"
        hybrid_car.fuels.append(p0)

        p1 = objects.Property()
        p1.name = "Battery"
        p1.value = "240 Volts"
        hybrid_car.fuels.append(p1)

        hybrid_car.save()

        loaded_hybrid = Hybrid(id=self.car._id)
        self.assertEqual(loaded_hybrid.fuels[0].name, hybrid_car.fuels[0].name)
        self.assertEqual(loaded_hybrid.fuels[0].value, hybrid_car.fuels[0].value)

    def tearDown(self):
        self.car.__class__.__remove__()


class Widget(unittest.TestCase):

    def setUp(self):
        self.car = objects.Car()
        self.car.make = "Isuzu"
        self.car.model = "Rodeo"
        self.car.year = datetime.datetime(2007, 1, 1)
        self.text_html= "<input name='make' value='Isuzu' id='id_make' type='text' class='red checked' />"
        self.choice_html = "<select class='Woot' id='id_car' name='car' ><option value='%s' >Isuzu Rodeo 2007-01-01 00:00:00</option></select>"
        self.object_html = """<ul class='test'>
                    <li>Make: Isuzu</li>
                    <li>Model: Rodeo</li>
                    <li>Year: 2007-01-01 00:00:00</li>
                </ul>"""



    def test_render(self):
        anne = objects.Female()
        anne.name = "Anne"
        print anne._get("name").render()

    def test_multiple_select(self):
        anne = objects.Female()
        anne.name = "Anne"
        anne.jobs.append(objects.Job())
        anne.jobs.append(objects.Job())
        def yo(obj):
            for i in obj:
                return {"value":i.title, "display":i.employer}
        print widget.MultipleSelect(object=anne.jobs, item_render=yo).render()

    def test_input_render(self):
        text = widget.Input(object=self.car._get("make"), name="make").render(cls="red checked")
        self.assertEqual(text.strip(), self.text_html.strip())

    def test_choice_render(self):
        _id = self.car.save()
        select = self.choice_html % str(_id)
        obj = objects.BadHuman()
        text = widget.Select(object=obj._get("car"), item_render=objects.car_disp, name='car').render(cls="Woot")
        self.assertEqual(text.strip(), select.strip())

    def test_object_render(self):
        text = objects.CarDisplay(object=self.car).render(cls='test')
        self.assertEqual(text.strip(), self.object_html.strip())

    def test_checkbox(self):
        obj = objects.BadHuman()
        text = widget.CheckBox(object=obj._get("active")).render()
        print text
        with self.assertRaises(Exception) as cm:
            correct = text.index("CHECKED")
        obj.active = True
        checked = widget.CheckBox(object=obj._get("active")).render()
        print checked
        correct = checked.index("CHECKED")
        self.assertGreater(correct, -1)

class Form(unittest.TestCase):

    def setUp(self):
        self.obj = objects.BadHuman()
        self.obj.name = "Anne"
        self.obj.age = 27
        self.obj.height = 65
        self.obj.weight = 120
        self.submit = {
            "name":"",
            "human_id":"32226",
            "age":None,
            "weight":"175",
            "location-city":"Chicago",
            "location-state":"IL"
        }

    def test_form(self):
        form = objects.PersonForm(object=self.obj, data=self.submit)
        form.render()
        with self.assertRaises(orm.DocumentException) as e:
            form.validate()

    def test_iterator(self):
        form = objects.PersonForm(obj=self.obj, data=self.submit)
        for f in form:
            print f.label_tag()
            print f.render(cls="popup")
