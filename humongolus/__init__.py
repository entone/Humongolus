import settings as _settings
import datetime
import pymongo
from pymongo.objectid import ObjectId

EMPTY = ("", " ", None, "None")

def settings(logger, db_connection):
    _settings.LOGGER = logger
    _settings.DB_CONNECTION = db_connection
    ensure_indexes()

def import_class(kls):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m


class FieldException(Exception): pass
class DocumentException(Exception): 
    errors = {}
    def __init__(self, errors):
        Exception.__init__(self, "")
        self.errors = errors

class Widget(object):
    _object = None

    def __init__(self, obj):
        self._object = obj
    
    def clean(self, val, doc=None):
        return val
    
    def render(self, *args, **kwargs):
        return self._object.__repr__()

class Field(object):
    logger = None
    _name = None
    _conn = None
    _value = None
    _dirty = None
    _default = None
    _required = False
    _display = None
    _error = None
    _dbkey = None
    _widget = None
    _parent = None
    __kwargs__ = {}
    __args__ = ()

    def __init__(self, *args, **kwargs):
        self.logger = _settings.LOGGER
        self._conn = _settings.DB_CONNECTION
        self.__kwargs__ = kwargs
        self.__args__ = args
        for k,v in kwargs.iteritems():
            if hasattr(self, "_%s" % k): setattr(self, "_%s" % k, v)
        
        self._dirty = self.clean(self._default, doc=None) if self._default else None
        self._value = self.clean(self._default, doc=None) if self._default else None
        self._error = None

    def _clean(self, val, dirty=None, doc=None):
        if val in EMPTY and self._required: raise FieldException("Required Field")
        val = self.clean(val, doc=None)
        val = self._widget(self).clean(val, doc=doc) if self._widget else val
        self._dirty = self._value if not dirty else dirty
        self._value = val
    
    def clean(self, val, doc=None): return val
    
    def _json(self):
        return self._value
    
    def _save(self, namespace):
        obj = {}
        if self._value != self._dirty: obj[namespace] = self._value
        return obj
    
    def _errors(self, namespace):
        errors = {}
        if self._error: errors[namespace] = self._error
        return errors
    
    def _map(self, val, init=False, doc=None):
        if init: self._clean(val, dirty=val, doc=doc)
        else: self._clean(val, doc=doc)
    
    def render(self, *args, **kwargs):
        self._widget = kwargs.get("widget", self._widget)
        if self._widget: return self._widget(self).render(*args, **kwargs)
        return self._value
    
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self._value)
    
    def __unicode__(self):
        return unicode(self._value)

class Lazy(object):
    __kwargs__ = {}
    __args__ = ()
    _type = None
    _key = None
    _query = {}
    _parent = None
    _name = None
    _widget = None

    def __init__(self, *args, **kwargs):
        self.logger = _settings.LOGGER
        self.__args__ = args
        self.__kwargs__ = kwargs
        for k,v in kwargs.iteritems():
            if hasattr(self, "_%s" % k): setattr(self, "_%s" % k, v)

    
    def __call__(self, **kwargs):
        q = kwargs.get('query', {})
        q.update({self._key:self._parent._id})
        self._query.update(q)
        return self._type.find(self._query)

    def _save(self, *args, **kwargs): pass
    def _errors(self, *args, **kwargs): pass
    def _map(self, *args, **kwargs): pass
    def _json(self, *args, **kwargs): pass

    def render(self, *args, **kwargs):
        self._widget = kwargs.get("widget", self._widget)
        if self._widget: return self._widget(self).render(*args, **kwargs)
        return self.__repr__()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.__class__.__name__)
    
    def __unicode__(self):
        return unicode(self.__class__.__name__)

class List(list):
    logger = None
    _type = None
    _dbkey = None
    _parent = None
    _name = None
    _widget = None
    __kwargs__ = {}
    __args__ = ()


    def __init__(self, *args, **kwargs):
        self.logger = _settings.LOGGER
        self.__kwargs__ = kwargs
        self.__args__ = args
        for k,v in kwargs.iteritems():
            if hasattr(self, "_%s" % k): setattr(self, "_%s" % k, v)
        

    def append(self, obj):
        if isinstance(obj, self._type): 
            super(List, self).append(obj)
        else: raise Exception("%s not of type %s" % (obj.__class__.__name__, self._type.__name__))
    
    def _save(self, namespace):
        ret = {}
        for id, obj in enumerate(self):
            ns = ".".join([namespace, str(id)])
            try:
                if obj._inited: ret.update(obj._save(namespace=ns))
                else: ret.update({ns:obj._json()})
            except Exception as e:
                ret[ns] = obj
                print ret
        return ret
    
    def _errors(self, namespace):
        errors = {}  
        for id, obj in enumerate(self):
            ns = ".".join([namespace, str(id)])
            try:
                errors.update(obj._errors(namespace=ns))
            except Exception as e: pass
        return errors

           
    def _map(self, val, init=False, doc=None):
        for item in val:
            try:
                obj = self._type()
                obj._map(item, init=init, doc=None)
                self.append(obj)
            except:
                self.append(item)

    def _json(self):
        ret = []
        for obj in self:
            try:
                ret.append(obj._json())
            except:
                ret.append(obj)
        
        return ret
    
    def render(self, *args, **kwargs):
        self._widget = kwargs.get("widget", self._widget)
        if self._widget: return self._widget(self).render(*args, **kwargs)
        return self.__repr__()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.__class__.__name__)
    
    def __unicode__(self):
        return unicode(self.__class__.__name__)
        
class base(dict):
    logger = None
    _inited = False
    _parent = None
    _name = None
    _widget = None
    __kwargs__ = {}
    __args__ = ()
    __keys__ = []


    def __init__(self, *args, **kwargs):
        self.logger = _settings.LOGGER
        self.__kwargs__ = kwargs
        self.__args__ = args
        self._inited = False
        p = kwargs.get("parent", None)
        self._parent = p if p != self else None
        self.__keys__ = set()
        for cls in reversed(self.__class__._getbases()):
            for k,v in cls.__dict__.iteritems():
                if isinstance(v, (base, Field, List, Lazy)):
                    if not isinstance(v, Lazy): self.__keys__.add(unicode(k))
                    v.__kwargs__["parent"] = p
                    v.__kwargs__['name'] = k
                    self.__dict__[k] = v.__class__(*v.__args__, **v.__kwargs__)
    
    def __setattr__(self, key, val):
        try:
            fi = self.__dict__.get(key, None)
            fi._clean(val)  
        except FieldException as e:
            fi._error = e
        except Exception as e:
            self.__dict__[key] = val
    
    def __getattribute__(self, key):
        try:
            obj = object.__getattribute__(self, key)
            if isinstance(obj, Field): return obj._value
            else: return obj
        except Exception as e: raise e

    @classmethod
    def _getbases(cls):
        b = [cls]        
        for i in cls.__bases__:
            b.append(i)
            try:
                b.extend(i.__getbases__())
            except:pass
        return b
    
    def _get(self, key):
        try:
            return self.__dict__[key]
        except:
            raise AttributeError("%s is an invalid attribute") 


    def _save(self, namespace=None):
        obj = {}
        for k,v in self.__dict__.iteritems():
            ns = ".".join([namespace, k]) if namespace else k
            try:
                obj.update(v._save(namespace=ns))
            except Exception as e: pass 
        return obj
    
    def _errors(self, namespace=None):
        errors = {}
        for k,v in self.__dict__.iteritems():
            ns = ".".join([namespace, k]) if namespace else k
            try:
                errors.update(v._errors(namespace=ns))
            except Exception as e: pass
        return errors

    def _map(self, vals, init=False, doc=None):
        self._inited = True
        for k,v in vals.iteritems():
            try:
                self.__dict__.get(k, None)._map(v, init=init, doc=doc)
            except: pass

    def _json(self):
        obj = {}
        for k,v in self.__dict__.iteritems():
            try:
                if not isinstance(v, Lazy): 
                    obj[k] = v._json()
            except: pass
        
        return obj
    
    def render(self, *args, **kwargs):
        self._widget = kwargs.get("widget", self._widget)
        if self._widget: return self._widget(self).render(*args, **kwargs)
        return self.__repr__()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.__class__.__name__)
    
    def __unicode__(self):
        return unicode(self.__class__.__name__)

class EmbeddedDocument(base):pass

class Document(base):
    _id = None
    _db = None
    _collection = None
    _conn = None
    _coll = None
    _indexes = []
    __modified__ = None
    __created__ = None
    __active__ = True
    __hargs__ = {}
    __hargskeys__ = None

    def __init__(self, *args, **kwargs):
        kwargs['parent'] = self
        super(Document, self).__init__(*args, **kwargs)
        self._id = None
        self.__hargs__ = {}
        self.__hargskeys__ = set()
        self._conn = _settings.DB_CONNECTION
        self._coll = self._conn[self._db][self._collection]
        if kwargs.get('id', None): 
            self._id = ObjectId(kwargs['id'])
            self._doc()
    """
    this is called by pymongo for each key:val pair for each document 
    returned by find and find_one
    """ 
    def __setitem__(self, key, val):
        #_id is a built-in field, it won't be in self.__keys__
        if key != '_id':
            self.__hargs__[key] = val
            self.__hargskeys__.add(key)
            #an incomplete document from mongo will never call _map
            if self.__keys__.issubset(self.__hargskeys__) and self._id:
                self._map(self.__hargs__, init=True)
        else: self._id = val 

    def _doc(self):
        doc = self._coll.find_one({'_id':self._id})
        self._map(doc, init=True)

    @property
    def active(self): return self.__active__
    
    @property
    def created(self): return self.__created__

    @property
    def modified(self): return self.__modified__

    @classmethod
    def _connection(cls):
        _conn = _settings.DB_CONNECTION
        _coll = _conn[cls._db][cls._collection]
        return _coll

    @classmethod
    def find(cls, *args, **kwargs):
        if not kwargs.get("as_dict", None): kwargs['as_class'] = cls
        return cls._connection().find(*args, **kwargs)
    
    @classmethod
    def find_one(cls, *args, **kwargs):
        if not kwargs.get("as_dict", None): kwargs['as_class'] = cls
        return cls._connection().find_one(*args, **kwargs)    
    
    @classmethod
    def __ensureindexes__(cls):
        conn = cls._connection()
        for i in cls._indexes: i.create(conn)

    @classmethod
    def __remove__(cls, *args, **kwargs):
        cls._connection().remove(*args, **kwargs)
    
    @classmethod
    def __update__(cls, *args, **kwargs):
        cls._connection().update(*args, **kwargs)    

    def remove(self):
        self.__class__.__remove__({"_id":self._id})
    
    def update(self, update, **kwargs):
        self.__class__.__update__({"_id":self._id}, update, **kwargs)
    

    def json(self):
        obj = self._json()
        obj['_id'] = self._id
        obj['__active__'] = self.active
        obj['__created__'] = self.created
        obj['__modified__'] = self.modified
        return obj

    def save(self):
        errors = self._errors()
        if len(errors.keys()):
            self.logger.error(errors) 
            raise DocumentException(errors)
        if not self._id:
            self._save()
            self.__created__ = datetime.datetime.utcnow()
            self.__modified__ = datetime.datetime.utcnow()
            self.__active__ = True
            obj = self._json()
            obj['__created__'] = self.__created__
            obj['__modified__']= self.__modified__
            obj['__active__'] = self.__active__
            try:
                self._id = self._coll.insert(obj, safe=True)
            except Exception as e:
                self.logger.exception(e) 
                return False

                
        else:
            obj = self._save()
            self.__modified__ = datetime.datetime.utcnow()
            obj['__modified__'] = self.__modified__
            up = {'$set':obj}
            try:
                self._coll.update({'_id':self._id}, up, safe=True)
            except: return False
        return self._id

class Index(object):
    DESCENDING = pymongo.DESCENDING
    ASCENDING = pymongo.ASCENDING
    GEO2D = pymongo.GEO2D
    _name = None
    _name = None
    _key = None
    _drop_dups = None
    _unique = None
    _background = None
    _min = -180
    _max = 180

    def __init__(self, name, **kwargs):
        self._name = name
        for k,v in kwargs.iteritems():
            if hasattr(self, "_%s" % k): setattr(self, "_%s" % k, v)
    
    def create(self, conn):
        if not isinstance(self._key, list): self._key = [self._key]
        conn.ensure_index(self._key, drop_dups=self._drop_dups, background=self._background, unique=self._unique, min=self._min, max=self._max, name=self._name)


def ensure_indexes():
    for cls in Document.__subclasses__():
        _settings.LOGGER.debug("Starting Indexing: %s" % cls.__name__)
        cls.__ensureindexes__()
        _settings.LOGGER.debug("Done Indexing: %s" % cls.__name__)




