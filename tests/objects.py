import humongolus as orm
import datetime
import humongolus.field as field
import humongolus.widget as widget

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
    name = field.Char(required=True, min=2, max=25, widget=orm.Widget)
    age = field.Integer(min=0, max=3000)
    height = field.Float(min=1, max=100000)
    weight = field.Float(min=1)
    jobs = orm.List(type=Job)
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
        """ % (kwargs.get("cls", ""), self._object.make, self._object.model, self._object.year)


class Scion(Car):
    any_owner = field.DynamicDocument()
    make = field.Char(default="Scion")
    model = field.Char(default="xA")
    year = field.Date(default=datetime.datetime(2007, 1, 1))
    silly_date = field.TimeStamp()

class Rodeo(Car):
    tires = orm.List(type=int)

class BadHuman(Human):
    unique = field.Integer()
    email = field.Email()
    phone = field.Phone()
    car = field.ModelChoice(type=Car, widget=widget.Select, display=car_disp)
    active = field.Boolean(widget=widget.CheckBox)

Human.cars = orm.Lazy(type=Car, key='owner')