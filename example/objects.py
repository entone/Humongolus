import humongolus as orm
import datetime
import humongolus.field as field
import humongolus.widget as widget
from pymongo.connection import Connection

def car_disp(car):
    return {"value":car._id, "display":"%s %s %s" % (car.make, car.model, car.year)}

class Location(orm.EmbeddedDocument):
    city = field.Char(required=True)
    state = field.Char()

class LocationGeo(Location):
    geo = field.Geo()
    active = field.Boolean()

class Job(orm.EmbeddedDocument):
    employer = field.Char()
    title = field.Char(required=True)
    locations = orm.List(type=Location)

class Human(orm.Document):
    _db = "test"
    _collection = "humans"
    _indexes = [
        orm.Index("name", key=[("name", orm.Index.DESCENDING)]), 
        orm.Index("human_id", key=[("human_id", orm.Index.ASCENDING)]),
        orm.Index("geo_location", key=[("jobs.locations.geo", orm.Index.GEO2D)])
    ]
    human_id = field.AutoIncrement(collection="human")
    name = field.Char(required=True, min=2, max=25)
    age = field.Integer(min=0, max=3000)
    height = field.Float(min=1, max=100000)
    weight = field.Float(min=1)
    jobs = orm.List(type=Job, length=3)
    genitalia = field.Char()

class Female(Human):
    genitalia = field.Char(default='inny')

class Male(Human):
    genitalia = field.Char(default='outy')

class Car(orm.Document):
    _db = "test"
    _collection = "cars"
    owner = field.DocumentId(type=Human)
    make = field.Char()
    model = field.Char()
    year = field.Date()

class CarDisplay(orm.Widget):
    #ideally you're using some sort of templating engine, I prefer Mako.
    def render(self, *args, **kwargs):
        return """
                <ul class='%s'>
                    <li>Make: %s</li>
                    <li>Model: %s</li>
                    <li>Year: %s</li>
                </ul>
        """ % (kwargs.get("cls", ""), self.object.make, self.object.model, self.object.year)


class Scion(Car):
    any_owner = field.DynamicDocument()
    color = field.Choice(choices=["Red", "Blue", "Green"])
    make = field.Char(default="Scion")
    model = field.Char(default="xA")
    year = field.Date(default=datetime.datetime(2007, 1, 1))
    silly_date = field.TimeStamp()

class Rodeo(Car):
    tires = orm.List(type=int)


class StateValidator(orm.FieldValidator):

    def validate(self, val, doc=None):
        print("Test!")
        print(self.obj._base.__class__.__name__)
        if val and not self.obj._parent.country is "USA": raise field.FieldException("Country must be USA to have a state")
        return val

class Address(orm.EmbeddedDocument):
    street = field.Char(required=True)
    zip = field.Char()

class Loca(orm.EmbeddedDocument):
    city = field.Char(required=True)
    address = Address()

class BadHuman(Human):
    unique = field.Integer()
    phone = field.Phone()
    email = field.Email(dbkey="em")
    car = field.ModelChoice(type=Car)
    active = field.Boolean()
    location = Loca()
    avatar = field.File(database=Connection().avatars)

Human.cars = orm.Lazy(type=Car, key='owner')


class AddressForm(widget.FieldSet):
    _fields = ["street", "zip"]

    street = widget.Input(label="Street")
    zip = widget.Input(label="Zip")

class LocationForm(widget.FieldSet):
    _fields = ["city", "address"]

    city = widget.Input(label="City")
    address = AddressForm(label="Address")

class HumanForm(widget.Form):
    #if anyone knows a better way to maintain the order of the fields, please let me know!
    _fields = ["name", "age", "weight", "location"]

    name = widget.Input(label="Name")
    age = widget.Input(label="Age", description="This is today minus the date you were born in seconds.")
    weight = widget.Input(label="Weight")
    location = LocationForm(label="Location")

class SimpleForm(widget.Form):
    _fields = ["name", "age", "phone"]
    name = widget.Input(label="Name")
    age = widget.Input(label="Age", description="This is today minus the date you were born in seconds.")
    phone = widget.Input(label="Phone")


