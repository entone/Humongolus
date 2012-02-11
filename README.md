# Humongolus | A Python ORM for MongoDB

## Features
* Strict Type Checking
* Lazy Relationships
* Fully Featured Indexes
* Dirty Updating (only send changes to db)
* Exposes default MongoDB cursors 
* Widget System for Fields
* Large Collection of Default Field Types
    * Char
    * Integer
    * Float
    * Date
    * TimeStamp
    * DocumentID (pseudo DBRef)
    * AutoIncrement
    * DynamicDocument (pseudo DBRef)
    * Geo (coming soon)
    * Email (coming soon)
    * Phone (coming soon)
* Endless EmbeddedDocuments
* Default Created/Modified attributes
* Plugins (coming soon) 

### Usage

    from pymongo.connection import Connection
    import logging
    import humongolus as orm
    import datetime
    import humongolus.field as field

    conn = Connection()
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger("humongolus")

    orm.settings(logger=logger, db_connection=conn)

    class Location(orm.EmbeddedDocument):
        city = field.Char(required=True)
        state = field.Char()

    class Job(orm.EmbeddedDocument):
        employer = field.Char()
        title = field.Char(required=True)
        locations = orm.Relationship(type=Location)

    class Human(orm.Document):
        _db = "test"
        _collection = "humans"
        human_id = field.AutoIncrement(collection="human")
        name = field.Char(required=True, min=2, max=25)
        age = field.Integer(min=0, max=3000)
        height = field.Float(min=1, max=100000)
        weight = field.Float(min=1, max=30000)
        jobs = orm.Relationship(type=Job)
        genitalia = field.Char()

    class Female(Human):
        genitalia = field.Char(default='inny')

    class Male(Human):
        genitalia = field.Char(default='outy')

    class Car(orm.Document):
        _db = "test"
        _collection = "cars"
        owner = field.DynamicDocument()
        make = field.Char()
        model = field.Char()
        year = field.Date()
        silly_date = field.TimeStamp()    

    Human.cars = orm.Lazy(type=Car, key='owner._id')

    chris = Male()
    chris.name = "Chris"
    chris.age = 31
    chris.height = 100
    chris.weight = 180

    job = Job()
    job.employer = "Entropealabs"
    job.title = "President"

    loc = Location()
    loc.city = "Chicago"
    loc.state = "IL"

    job.locations.append(loc)
    chris.jobs.append(job)

    print chris._json()
        {'jobs': [
            {
                'employer': u'Entropealabs', 
                'locations': [
                    {'city': u'Chicago', 'state': u'IL'}
                ], 
                'title': u'President'}
            ], 
            'name': u'Chris', 
            'weight': 180.0, 
            'age': 31, 
            'height': 100.0, 
            'genitalia': u'outy', 
            'human_id': 1328
        }

    _id = chris.save()

    print _id

        4f36dd48eac0742b92000000

    car = Car()
    car.owner = chris
    car.make = "Isuzu"
    car.model = "Rodeo"
    car.year = datetime.datetime(1998, 1, 1)

    print car
        <__main__.Car object at 0x7fe3c9375650>

    c_id = car.save()

    print car._get("owner")().name
        Chris
