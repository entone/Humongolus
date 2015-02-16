# Copyright 2012 Entropealabs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Humongolus is a Persistence and Widget Framework for MongoDB written in Python
"""

import settings as _settings
import mongo
import datetime
import pymongo
from bson.objectid import ObjectId

EMPTY = ("", " ", None, "None")

def settings(logger, db_connection):
    """Set the logger and MongoDB Connection

    Apply Model Indexes

    :Parameters:
        - `logger`: instance of the Python Logger class
        - `db_connection`: instance of a pymongo Connection class
    """
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

class FieldValidator(object):
    """Base class for custom field validation. Should always be extended.
    """
    obj = None

    def __init__(self, obj):
        self.obj = obj

    def validate(self, val, doc=None):
        """Override this method to apply custom validation for a field.

        self.obj is the Model attribute being set.

        through self.obj you have access to attributes _parent and _base
        _parent is the Document|EmbeddedDocument containing the current field
        _base is the base Document object if available

        :Parameters:
            - `val`: incoming value from a form or other assignment
            - `doc`: a dictionary available if using the Form system. The dictionary will contain all keys passed to the Form object on instantiation

        """
        return val

class BaseException(Exception):
    def json(self):
        return dict(
            type=self.__class__.__name__,
            message=self.message,
            status=self.status_code,
        )

class FieldException(BaseException):
    """Exception for field validation errors.
    """
    pass
class DocumentException(BaseException):
    """Exception thrown when an error/errors are raised when saving a Document
    """
    errors = {}
    def __init__(self, errors):
        """
        Create a new instance of DocumentException

        :Parameters:
            - `errors`: dictionary of errors
        """
        Exception.__init__(self, "")
        self.errors = errors

    def __str__(self):
        return str(self.errors)

    def json(self):
        return dict(
            type=self.__class__.__name__,
            message=self.message,
            status=self.status_code,
            errors=self.errors
        )


class InvalidObjectId(BaseException):
    status_code = 404

class Attributes(object):
    _id = None
    _name = None
    label = None
    description = None
    value = None
    cls = None
    cols = None
    rows = None
    prepend = None
    action = ""
    method = "POST"
    type = "multipart/form"
    action = None
    item_render = None
    extra = {}

    def __init__(self, **kwargs):
        self._name = kwargs.pop("name", None)
        self._id = kwargs.pop("id", None)
        for k,v in kwargs.iteritems():
            try:
                setattr(self, k, v)
            except Exception as e:
                print e

    @property
    def name(self):
        return "%s_%s" % (self.prepend, self._name) if self.prepend else self._name

    @property
    def id(self):
        return "%s_%s" % (self.prepend, self._id) if self.prepend else self._id

class Widget(object):
    """Base class for all widgets
    """
    __args__ = []
    __kwargs__ = {}
    _prepend = None
    _data = None
    errors = []
    attributes = Attributes()
    object = None

    def __init__(self, *args, **kwargs):
        """Create a new instance of a widget
        This is generally handled automatically when using the Form system

        :Parameters:
            - `object`: the object to render the widget with
            - `**kwargs`: attributes to be applied to the widget
        """
        self.__args__ = args
        self.__kwargs__ = kwargs
        self.object = kwargs.pop('object', None)
        self._data = kwargs.pop('data', None)
        self.errors = []
        kwargs['prepend'] = self._prepend if self._prepend and not 'prepend' in kwargs else kwargs.pop('prepend', None)
        self.attributes = Attributes(**kwargs)

        for k,v in self.__class__._getfields().iteritems():
            v.__kwargs__['prepend'] = self.attributes.prepend
            v.__kwargs__['name'] = k
            try:
                v.__kwargs__['object'] = self.object._get(k)
            except Exception as e: pass
            n_obj = v.__class__(*v.__args__, **v.__kwargs__)
            self.__dict__[k] = n_obj

    @classmethod
    def _getfields(cls):
        fields = {}
        for k,v in cls.__dict__.iteritems():
            if isinstance(v, Widget): fields[k]=v

        for i in cls.__bases__:
            try:
                fields.update(i._getfields())
            except:pass
        return fields

    def clean(self, val, doc=None):
        """Override to apply custom parsing of form data.
        This is called anytime you set the value of a Field.
        Should always return the "cleaned" value or raise a FieldException on error

        :Parameters:
            - `val`: incoming value from a form or other assignment
            - `doc`: a dictionary available if using the Form system. The dictionary will contain all keys passed to the Form object on instantiation
        """
        return val

    def render(self, *args, **kwargs):
        """Override to customize output

        Default returns self._object.__repr__()

        """
        return self.object.__repr__()

    def __call__(self, *args, **kwargs):
        parts = self.render(*args, **kwargs)
        if isinstance(parts, list):
            return "".join(parts)

        return parts

class Field(object):
    """Base class for all Field types

    :Parameters:
        - `name`: when used in a Model, this will be the attribute name, optional
        - `default`: default value, optional
        - `required`: whether or not the field is required, optional default to False
        - `display`: value for display purposes, this is used for labels when using the :class: `~widget.Form` widget, optional
        - `dbkey`: if the field name in the mongodb document is different then the Models attribute name, use this to indicate the mongo attribute name
        - `widget`: :class: `~Widget` to use for rendering, also assignable when creating a form, optional
        - `validate`: an instance :class: `~FieldValidator` for custom validation
    """

    logger = None
    _name = None
    _conn = None
    _value = None
    _dirty = None
    _default = None
    _required = False
    _error = None
    _dbkey = None
    _base = None
    _parent = None
    _validate = None
    __kwargs__ = {}
    __args__ = ()

    def __init__(self, *args, **kwargs):

        self.logger = _settings.LOGGER
        self._conn = _settings.DB_CONNECTION
        self.__kwargs__ = kwargs
        self.__args__ = args
        for k,v in kwargs.iteritems():
            try:
                setattr(self, "_"+k, v)
            except: pass

        self._dirty = self.clean(self._default, doc=None) if not self._default in EMPTY else None
        self._value = self.clean(self._default, doc=None) if not self._default in EMPTY else None
        self._error = None

    def __get__(self, instance, owner):
        me = instance.__dict__.get(self._name)
        if me:
            if callable(me): return me()
            return me._value

    def __set__(self, instance, value):
        me = instance.__dict__.get(self._name)
        if me:
            try:
                me._clean(value)
            except FieldException as e:
                me._error = e

    def _clean(self, val, dirty=None, doc=None):
        self._error = None
        self._isrequired(val)
        if not val in EMPTY:
            val = self.clean(val, doc=doc)
        val = self._validate(self).validate(val, doc=doc) if self._validate else val
        self._dirty = self._value if not dirty else dirty
        self._value = val

    def clean(self, val, doc=None):
        """Override to apply custom parsing of incoming value.
        This is called anytime you set the value of a Field.
        Should always return the "cleaned" value or raise a FieldException on error

        :Parameters:
            - `val`: incoming value from a form or other assignment
            - `doc`: a dictionary available if using the :class: `~Form` system. The dictionary will contain all keys passed to the :class: `~Form` object on instantiation
        """
        return val

    def _isrequired(self, val):
        if val in EMPTY and self._required: raise FieldException("Required Field")

    def _json(self):
        return self._value

    def _save(self, namespace):
        obj = {}
        if self._value != self._dirty:
            obj[namespace] = self._value
        return obj

    def _errors(self, namespace):
        errors = {}
        try:
            self._isrequired(self._value)
        except Exception as e:
            self._error = e
        if self._error: errors[namespace] = self._error
        return errors

    def _map(self, val, init=False, doc=None):
        try:
            if init:
                self._clean(val, dirty=val, doc=doc)
            else:
                self._clean(val, doc=doc)
        except Exception as e:
            self._error = e

    def render(self, *args, **kwargs): pass

    def __repr__(self):
        try:
            return self._value
        except Exception as e:
            return None

    def __str__(self):
        return str(self._value)

    def __unicode__(self):
        return unicode(self._value)

class Lazy(object):
    """Object for describing a "foreign key" relationship across Models"""
    __kwargs__ = {}
    __args__ = ()
    _type = None
    _key = None
    _query = {}
    _base = None
    _parent = None
    _name = None
    _dbkey = None
    _render = None
    _choices = []

    def __init__(self, *args, **kwargs):
        """
        :Parameters:
            - `type`: the type of :class: `~Document` returned. must be an instance of :class: `~Document`
            - `key`: the "foreign key" to look up the types by. must be an attribute of type.

        """
        self.logger = _settings.LOGGER
        self.__args__ = args
        self.__kwargs__ = kwargs
        self._query = {}
        for k,v in kwargs.iteritems():
            try:
                setattr(self, "_"+k, v)
            except: pass


    def __call__(self, **kwargs):
        """when calling the lazy object it will return a mongodb cursor that yields models of the type.
        It will use the the _id of the base document and look in the key of the type class
        """
        q = kwargs.pop('query', {})
        q.update({self._key:self._base._id})
        self._query.update(q)
        self.logger.info(self._query)
        return self._type.find(self._query, **kwargs)

    def _save(self, *args, **kwargs): pass
    def _errors(self, *args, **kwargs): pass
    def _map(self, *args, **kwargs): pass
    def _json(self, *args, **kwargs): pass

    def render(self, *args, **kwargs): pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.__class__.__name__)

    def __unicode__(self):
        return unicode(self.__class__.__name__)

class List(list):
    """Used to describe an array in a :class: `~Document` or :class: `~EmbeddedDocument`. Extends list."""
    logger = None
    _type = None
    _length = None
    _dbkey = None
    _base = None
    _parent = None
    _name = None
    _render = None
    __kwargs__ = {}
    __args__ = ()


    def __init__(self, *args, **kwargs):
        """
        :Parameters:
            - `type`: the type of :class: `~Document` returned. must be an instance of :class: `~Document`, can be an array
            - `length`: maximum length of the array
            - `dbkey`: if the field name in the mongodb document is different then the Models attribute name, use this to indicate the mongo attribute name
            - `widget`: :class: `~Widget` to use for rendering, also assignable when creating a form, optional
        """
        self.logger = _settings.LOGGER
        self.__kwargs__ = kwargs
        self.__args__ = args
        self._inited = False
        for k,v in kwargs.iteritems():
            try:
                setattr(self, "_"+k, v)
            except: pass


    def append(self, obj):
        types = self._type if self._type.__class__ is list else [self._type]
        if self._length and len(self) >= self._length: raise Exception("max length: %s exceeded" % self._length)
        if obj.__class__ in types:
            super(List, self).append(obj)
        else: raise Exception("%s not of type %s" % (obj.__class__.__name__, self._type.__name__))

    def _save(self, namespace):
        ret = {}
        if len(self) == 0: return {namespace:[]}
        if not self._inited: return {namespace:self._json()}
        for id, obj in enumerate(self):
            ns = ".".join([namespace, str(id)])
            try:
                if obj._inited: ret.update(obj._save(namespace=ns))
                else: ret.update({ns:obj._json()})
            except Exception as e:
                ret[ns] = obj
        return ret

    def delete(self, query, key):
        ob = self[key]
        self._base._coll.update({'_id':self._base._id}, {'$pull':{query:ob}})
        del self[key]

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
            self._inited = True
            try:
                obj = self._type()
                try:
                    item = item.__hargs__
                except:pass
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

    def get_choices(self, render=None):
        if render:
            return render(obj=self)
        else: return [i for i in self]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.__class__.__name__)

    def __unicode__(self):
        return unicode(self.__class__.__name__)

class base(dict):
    logger = None
    _inited = False
    _base = None
    _parent = None
    _name = None
    _dbkey = None
    _bases = None
    _fields = {}
    __kwargs__ = {}
    __args__ = ()
    __keys__ = []
    __doc__ = {}

    def __new__(cls, *args, **kwargs):
        if not cls._bases or cls._bases[0] != cls:
            cls._bases = cls._getbases()
            cls._fields = {}
            cls.__keys__ = set()
            for c in reversed(cls._bases):
                for k,v in c.__dict__.iteritems():
                    if isinstance(v, (base, Field, List, Lazy)):
                        key = v._dbkey if v._dbkey else k
                        if not isinstance(v, Lazy): cls.__keys__.add(unicode(key))
                        v._name = k
                        cls._fields[k] = v

        return super(base, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        self.logger = _settings.LOGGER
        self.__kwargs__ = kwargs
        self.__args__ = args
        self._inited = False
        b = kwargs.get("base", None)
        self._base = b if b != self else None
        for k,v in self._fields.iteritems():
            v.__kwargs__["base"] = b
            v.__kwargs__['name'] = k
            v.__kwargs__['parent'] = self
            v._name = k
            self.__dict__[k] = v.__class__(*v.__args__, **v.__kwargs__)

    def __nonzero__(self):
        return True

    @classmethod
    def _getbases(cls, b=None):
        if not b: b = [cls]
        else: b.append(cls)
        for i in cls.__bases__:
            try:
                b = i._getbases(b=b)
            except:pass
        return b

    def _get(self, key):
        try:
            return self.__dict__[key]
        except:
            raise AttributeError("%s is an invalid attribute" % key)


    def _save(self, namespace=None):
        obj = {}
        for k,v in self.__dict__.iteritems():
            try:
                key = v._dbkey if v._dbkey else k
                ns = ".".join([namespace, key]) if namespace else key
                obj.update(v._save(namespace=ns))
            except Exception as e: pass
        return obj

    def _errors(self, namespace=None):
        errors = {}
        for k,v in self.__dict__.iteritems():
            try:
                key = v._dbkey if v._dbkey else k
                ns = ".".join([namespace, key]) if namespace else key
                errors.update(v._errors(namespace=ns))
            except Exception as e: pass
        return errors

    def _map(self, vals, init=False, doc=None):
        self._inited = True
        for k,v in self.__dict__.iteritems():
            try:
                key = v._dbkey if v._dbkey else k
                val = vals[key]
                v._map(val, init=init, doc=doc)
            except Exception as e: pass

    def _json(self):
        obj = {}
        for k,v in self.__dict__.iteritems():
            try:
                if not isinstance(v, Lazy):
                    key = v._dbkey if v._dbkey else k
                    obj[key] = v._json()
            except: pass

        return obj

    def render(self): pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.__class__.__name__)

    def __unicode__(self):
        return unicode(self.__class__.__name__)

class EmbeddedDocument(base):
    """Base class for all emdedded documents
    """
    pass

class Document(base):
    """Base class for all first level documents. This will contain the _id and has the "save" method.

    All models should extend this class.

    When extending always set _db and _collection. These tell humongolus where to save and find it's documents.

    _indexes is used to set the mongo indexes, it should be an array of :class: `~Index` objects

    """
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
        kwargs['base'] = self
        super(Document, self).__init__(*args, **kwargs)
        self._id = None
        self.__hargs__ = {}
        self.__hargskeys__ = set()
        self._conn = _settings.DB_CONNECTION
        self._coll = self.__class__._connection()
        if kwargs.get('data'):
            init = kwargs.get("init", True)
            self._map(kwargs.get('data'), init=init)
        if kwargs.get('id'):
            self._doc(kwargs['id'])
    """
    this is called by pymongo for each key:val pair for each document
    returned by find and find_one
    """
    def __setitem__(self, key, val):
        #_id is a built-in field, it won't be in self.__keys__
        if key != '_id':
            try:
                self.__hargs__[key] = val.__hargs__
            except:
                self.__hargs__[key] = val
            self.__hargskeys__.add(key)
            #an incomplete document from mongo will never call _map
            if self.__keys__.issubset(self.__hargskeys__) and self._id:
                self._map(self.__hargs__, init=True)
        elif key == '_id': self._id = val

    def _get_doc(self, id):
        return _settings.DB_CONNECTION[self._db][self._collection].find_one({'_id':ObjectId(id)})

    def _doc(self, id):
        doc = self._get_doc(id)
        if not doc: raise InvalidObjectId(id)
        self._map(doc, init=True)

    @property
    def active(self):
        """is document active: Boolean
        """
        return self.__active__

    @property
    def created(self):
        """created date of document: datetime
        """
        return self.__created__

    @property
    def modified(self):
        """return last modify date of document. updated after every successful save: datetime
        """
        return self.__modified__

    @classmethod
    def _connection(cls):
        _conn = _settings.DB_CONNECTION
        _coll = mongo.Collection(cls, database=_conn[cls._db], name=cls._collection)
        return _coll

    @classmethod
    def find(cls, *args, **kwargs):
        """returns pymongo cursor that yields instantiated Document objects of the Class type.
        :Parameters:
            - `*args`: passed directly to Connection.find()
            - `**kwargs`: passed directly to Connection.find()

        extra kwargs paramter is as_dict this will return the raw dictionary from mongo, this also allows you to use the "fields" parameter
        """

        return cls._connection().find(*args, **kwargs)

    @classmethod
    def find_one(cls, *args, **kwargs):
        """returns single instantiated Document object of the Class type.
        :Parameters:
            - `*args`: passed directly to Connection.find_one()
            - `**kwargs`: passed directly to Connection.find_one()
        """
        return cls._connection().find_one(*args, **kwargs)

    @classmethod
    def __ensureindexes__(cls):
        try:
            conn = cls._connection()
        except: pass

        for i in cls._indexes: i.create(conn)

    @classmethod
    def __remove__(cls, *args, **kwargs):
        cls._connection().remove(*args, **kwargs)

    @classmethod
    def __update__(cls, *args, **kwargs):
        cls._connection().update(*args, **kwargs)

    def remove(self):
        """Remove document. Calls .remove on pymongo Connection

        """
        self.__class__.__remove__({"_id":self._id})

    def update(self, update, query={}, **kwargs):
        """Update itself. Allows for custom saving, ie; not using safe=True
        """
        q = {"_id":self._id}
        q.update(query)
        self.__class__.__update__(q, update, **kwargs)

    def _map(self, vals, *args, **kwargs):
        self.__created__ = vals.get('__created__', self.__created__)
        self.__modified__ = vals.get('__modified__', self.__modified__)
        self.__active__ = vals.get('__active__', self.__active__)
        id = vals.get('_id')
        if id: self._id = ObjectId(id)
        super(Document, self)._map(vals, *args, **kwargs)


    def json(self):
        """Return json representation of itself.
        """
        obj = self._json()
        obj['_id'] = self._id
        obj['__active__'] = self.active
        obj['__created__'] = self.created
        obj['__modified__'] = self.modified
        return obj

    def save(self):
        """use this method to write a new object to the database or to save en existing document after updating.

        if the document already exists it will send an atomic update of only the changed attributes to mongo.

        always uses safe=True

        will raise a DocumentException if there are errors from validation, will also throw a pymongo Exception if insert or update fails.

        """
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
            self._id = self._coll.insert(obj, safe=True)
        else:
            obj = self._save()
            self.__modified__ = datetime.datetime.utcnow()
            obj['__modified__'] = self.__modified__
            up = {'$set':obj}
            self._coll.update({'_id':self._id}, up, safe=True)
        return self._id

class Index(object):
    DESCENDING = pymongo.DESCENDING
    ASCENDING = pymongo.ASCENDING
    GEO2D = pymongo.GEO2D
    _name = None
    _key = None
    _drop_dups = None
    _unique = None
    _background = None
    _ttl = None
    _min = -180
    _max = 180
    _sparse = False

    def __init__(self, name, **kwargs):
        self._name = name
        for k,v in kwargs.iteritems():
            if hasattr(self, "_%s" % k): setattr(self, "_%s" % k, v)

    def create(self, conn):
        if not isinstance(self._key, list): self._key = [self._key]
        ob = dict(
            drop_dups=self._drop_dups,
            background=self._background,
            unique=self._unique,
            min=self._min,
            max=self._max,
            name=self._name,
            sparse=self._sparse,
        )
        if self._ttl: ob['expireAfterSeconds'] = self._ttl
        conn.ensure_index(self._key, **ob)

def ensure_indexes(typ=Document):
    for cls in typ.__subclasses__():
        try:
            _settings.LOGGER.debug("Starting Indexing: %s" % cls.__name__)
            cls.__ensureindexes__()
            _settings.LOGGER.debug("Done Indexing: %s" % cls.__name__)
            ensure_indexes(cls)
        except Exception as e:
            _settings.LOGGER.warning(e)
