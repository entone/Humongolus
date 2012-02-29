from pymongo.connection import Connection
import logging
import humongolus as orm
import datetime
import humongolus.field as field
import humongolus.widget as widget
from states import states

conn = Connection()
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("humongolus")

orm.settings(logger=logger, db_connection=conn)

class Car(orm.Document):
    _db = "test"
    _collection = "cars"
    owner = field.DynamicDocument()
    make = field.Char()
    model = field.Char()
    year = field.Date()
    silly_date = field.TimeStamp()

Car.__remove__()

class Address(orm.EmbeddedDocument):
    street = field.Char()
    street2 = field.Char()
    zip = field.Char()


class Location(orm.EmbeddedDocument):
    city = field.Char(required=True)
    state = field.Char()
    address = Address()

class Job(orm.EmbeddedDocument):
    employer = field.Char()
    title = field.Char(required=True)
    locations = orm.List(type=Location)


class Human(orm.Document):
    _db = "test"
    _collection = "humans"
    human_id = field.AutoIncrement(collection="human")
    name = field.Char(required=True, min=2, max=25)
    age = field.Integer(required=True, min=0, max=3000)
    height = field.Float(min=1, max=100000)
    weight = field.Float(min=1, max=30000)
    jobs = orm.List(type=Job)
    genitalia = field.Char()
    location = Location()
    car = field.ModelChoice(type=Car)
    color = field.Choice(choices=[{'value':'red', 'display':'Red'},{'value':'blue', 'display':'Blue'},{'value':'green', 'display':'Green'}])
    state = field.CollectionChoice(db='test', collection='states', sort=[('fullname',1)])

class Female(Human):
    genitalia = field.Char(default='inny')

class Male(Human):
    genitalia = field.Char(default='outy')
    
class CarDisplay(orm.Widget):
    #ideally you're using some sort of templating engine, I prefer Mako.
    def render(self, *args, **kwargs):
        return """
                <ul class='%s'>
                    <li>Make: %s</li>
                    <li>Model: %s</li>
                    <li>Year: %s</li>
                </ul>
        """ % (kwargs.get("cls", ""), self._object.make, self._object.model, self._object.year)

Human.cars = orm.Lazy(type=Car, key='owner._id')

chris = Male()
chris.name = "Chris"
chris.age = 31
chris.height = 100
chris.weight = 180
chris.location.city = "Chicago"
chris.location.state = "IL"
chris.location.address.zip = 60626

job = Job()
job.employer = "Entropealabs"
job.title = "President"

loc = Location()
loc.city = "Chicago"
loc.state = "IL"

job.locations.append(loc)
chris.jobs.append(job)

print chris._json()

_id = chris.save()

print _id

car = Car()
car.owner = chris
car.make = "Isuzu"
car.model = "Rodeo"
car.year = datetime.datetime(1998, 1, 1)
print car
c_id = car.save()

car2 = Car()
car2.owner = chris
car2.make = "Mercedes"
car2.model = "Baby C"
car2.year = datetime.datetime(1965, 1, 1)
print car2
c_id = car2.save()

print car._get("owner")().name


def car_disp(car):
    return {"value":car._id, "display":"%s %s %s" % (car.make, car.model, car.year)}

def coll_display(doc):
    return {'value':doc.get('abbrv'), 'display':doc.get('fullname', None)}

def job_list(obj):
    ar = []
    for i in obj:
        ar.append({"value":i.title, "display":"%s: %s" % (i.employer, i.title)})
    return ar

class AddressForm(widget.FieldSet):
    _fields = ["street", "street2", "zip"]

    street = widget.Input(cls="woot")
    street2 = widget.Input()
    zip = widget.Input()

class LocationForm(widget.FieldSet):
    _fields = ["city", "state", "address"]
    _cls = "location"

    city = widget.Input()
    state = widget.Input()
    address = AddressForm()

class PersonForm(widget.Form):
    _action = '/save_person'
    _id = "person_%s" % chris._id
    #if anyone knows a better way to maintain the order of the fields, please let me know!
    _fields = ["human_id", "name", "age", "car", "location", "jobs"]

    human_id = widget.Input(label="ID")
    name = widget.Input(label="Name")
    age = widget.Input(label="Age", description="This is today minus the date you were born in seconds.")
    car = widget.Select(label="Car", render=car_disp)
    location = LocationForm(label="Location")
    jobs = widget.MultipleSelect(label="Jobs", render=job_list)

submit = {
    "name":"None",
    "human_id":"32226",
    "age":None,
    "weight":"175",
    "car":"ffed81a42000002",
    "location-city":"Chicago",
    "location-state":"IL",
    "location-address-street":"549 Randolph",
    "location-address-street2":"450",
    #"location-address-zip":"60626"
}

print states
conn['test']['states'].remove()
for k,v in states.iteritems():
    conn['test']['states'].insert({"abbrv":k, 'fullname':v})
    

class SelectorForm(widget.Form):
    _fields = ['car', 'color', 'state']
    car = widget.Select(label="Car", render=car_disp)
    color = widget.Select(label="Color")
    state = widget.Select(label="State", render=coll_display)

print "SELECTS:"

a = SelectorForm(object=chris)
print a.render()

form = PersonForm(object=chris, data=submit)

print form.car.render(cls="try-this")

print form.render()

try:
    form.validate()
except orm.DocumentException as e:
    for f in form:
        if f.errors:
            print f.name
            if f.description: print f.description
            print f.errors
    
    print form.errors
    print e.errors










