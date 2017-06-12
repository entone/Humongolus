"""
python insert 0.205296039581
bare 0.101219892502

python read 0.10541009903
bare 0.0112569332123

pypy insert 0.626013040543
bare 0.136276006699

pypy read 0.326532125473
bare 0.0427839756012
"""

from pymongo.mongo_client import MongoClient
import logging
import humongolus as orm
import datetime
import time
import humongolus.field as field

conn = MongoClient()
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("humongolus")

orm.settings(logger=logger, db_connection=conn)

class Job(orm.EmbeddedDocument):
	title = field.Char()

class Human(orm.Document):
    _db = "test"
    _collection = "humans"
    name = field.Char(required=True, min=2, max=25)
    age = field.Integer(min=0, max=3000)
    height = field.Float(min=1, max=100000)
    weight = field.Float(min=1, max=30000)
    jobs = orm.List(type=Job)
    genitalia = field.Char()

Human.__remove__()

start = time.time()
for i in range(100):
	human = {
		"name":"Chris",
		"age": 31,
		"height":120,
		"weight":180,
		"jobs":[],
		"genitalia":"outy"
	}
	conn['test']['humans'].insert(human, safe=True)
bare = time.time()-start
print(bare)

Human.__remove__()

orm_start = time.time()
for c in range(100):
	human = Human()
	human.name = "Chris"
	human.age = 31
	human.height = 120
	human.weight = 180
	human.genitalia = "outy"
	human.save()
orm_time = time.time()-orm_start
print(orm_time)

bare_get = time.time()
for c in conn["test"]["humans"].find():
	print("BARE: %s" % c.get("name", None))
bare_finish = time.time()-bare_get
print(bare_finish)

print("NEXT")

orm_get = time.time()
for c in Human.find():
	print("ORM: %s" % c.name)
orm_finish = time.time()-orm_get
print(orm_finish)
