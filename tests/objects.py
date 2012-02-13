import humongolus as orm
import datetime
import humongolus.field as field

class Location(orm.EmbeddedDocument):
    city = field.Char(required=True)
    state = field.Char()

class LocationGeo(Location):
    geo = field.Geo()
    active = field.Boolean()

class Job(orm.EmbeddedDocument):
    employer = field.Char()
    title = field.Char(required=True)
    locations = orm.Relationship(type=Location)

class Human(orm.Document):
    _db = "test"
    _collection = "humans"
    human_id = field.AutoIncrement(collection="human")
    name = field.Char(required=True, min=2, max=25, widget=orm.Widget)
    age = field.Integer(min=0, max=3000)
    height = field.Float(min=1, max=100000)
    weight = field.Float(min=1)
    jobs = orm.Relationship(type=Job)
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

class Scion(Car):
    any_owner = field.DynamicDocument()
    make = field.Char(default="Scion")
    model = field.Char(default="xA")
    year = field.Date(default=datetime.datetime(2007, 1, 1))
    silly_date = field.TimeStamp()

class Rodeo(Car):
    tires = orm.Relationship(type=int)

class BadHuman(Human):
    unique = field.Integer()
    email = field.Email()
    phone = field.Phone()

Human.cars = orm.Lazy(type=Car, key='owner')