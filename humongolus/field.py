import datetime
from humongolus import Field, FieldException, Document, import_class
from pymongo.objectid import ObjectId

class MinException(FieldException): pass
class MaxException(FieldException): pass

class Char(Field):
    _max=None
    _min=None
    _type = unicode
    _display = "string"

    def clean(self, val, doc=None):
        try:            
            val = self._type(val)
            if self._max != None and len(val) > self._max: raise MaxException("must be less than %s" % self._max)
            if self._min != None and len(val) < self._min: raise MinException("must be greater than %s" % self._min)
            return val
        except FieldException as e: raise e
        except: raise FieldException("%s is not a valid %s" % (val, self._display))

class Integer(Char):
    _type=int
    _display="integer"

    def clean(self, val, doc=None):
        try:            
            val = self._type(val)
            if self._max != None and val > self._max: raise MaxException("must be less than %s" % self._max)
            if self._min != None and val < self._min: raise MinException("must be greater than %s" % self._min)
            return val
        except FieldException as e: raise e
        except: raise FieldException("%s is not a valid %s" % (val, self._display))

class Float(Integer):
    _type=float
    _display="float"

class Date(Field):

    def clean(self, val, doc):
        try:
            if isinstance(val, datetime.datetime): return val
            return datetime.datetime(val)
        except: raise FieldException("%s: invalid datetime" % val)


class TimeStamp(Date):

    def _save(self, namespace):
        if self._value == None:
            self._value = datetime.datetime.utcnow()
        
        return super(TimeStamp, self)._save(namespace)

class DocumentId(Field):
    _type = None

    def clean(self, val, doc=None):
        val = val._id if hasattr(val, '_id') else val
        v = ObjectId(val)
        return v
    
    def __call__(self):
        if self._value and self._type:
            return self._type(id=self._value)
        else: raise FieldException("Cannot instantiate %s with id %s" % (self._type, self._value))


class AutoIncrement(Integer):
    _collection = None

    def _save(self, namespace):
        if self._value == None:
            col = self._collection if self._collection else "sequence"
            res = self._conn["auto_increment"][col].find_and_modify({"field":self._name}, {"$inc":{"val":1}}, upsert=True, new=True, fields={"val":True})
            self._value = res['val']
        
        return super(AutoIncrement, self)._save(namespace)

class DynamicDocument(Field):

    def clean(self, val, doc=None):
        if isinstance(val, Document):
            if val._id != None:
                cls = "%s.%s" % (val.__module__, val.__class__.__name__)
                return {"cls":cls, "_id":val._id}
            else: raise FieldException("Document does not have an id. Be sure to save first.")
        elif isinstance(val, dict): 
            return val
        else: raise FieldException("%s is not a valid document type" % val.__class__.__name__)
    
    def __call__(self):
        if isinstance(self._value, dict):
            cls = import_class(self._value['cls'])
            return cls(id=self._value['_id'])
        else: raise Exception("Bad Value: %s" % self._value)


