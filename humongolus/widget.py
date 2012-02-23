import copy
from humongolus import Widget, Field, Document, EmbeddedDocument, Lazy, List, DocumentException

class HTMLElement(Widget):
    _tag = "input"
    _type = "text"
    _name = None
    _value = None
    _cls = None
    _extra = None
    _id = None

class Input(HTMLElement):
    
    def render(self, *args, **kwargs):
        self._type = kwargs.get("type", self._type)
        self._name = kwargs.get("namespace", self._object._name)
        self._value = kwargs.get("value", self._object.__repr__())
        self._id = kwargs.get("id", "id_%s"%self._name) 
        self._cls = kwargs.get("cls", "")
        self._extra = kwargs.get("extra", "")
        return "<%s type='%s' id='%s' name='%s' value='%s' class='%s' %s />" % (self._tag, self._type, self._id, self._name, self._value, self._cls, self._extra)

class Password(Input):
    _type = "password"

class CheckBox(Input):
    _type = "checkbox"

    def render(self, *args, **kwargs):
        extra = "checked='CHECKED'" if self._object._value else ""
        kwargs["extra"] = extra
        kwargs["value"] = self._object._name
        return super(CheckBox, self).render(*args, **kwargs)

class Select(Input):

    def render(self, *args, **kwargs):
        val = super(Select, self).render(*args, **kwargs)
        st = "<select id='%s' name='%s' class='%s'>" % (self._id, self._name, self._cls)
        ch = []
        for i in self._object._choices:
            val = i['value'] if isinstance(i, dict) else i
            display = i['display'] if isinstance(i, dict) else i
            ch.append("<option value='%s'>%s</option>" % (val, display))
        
        return "%s%s</select>" % (st, "".join(ch))


class FormField(object):
    _widget = None
    _label = None
    _cls = None
    _object = None
    __kwargs__ = {}
    __allkwargs__ = {}
    
    def __init__(self, **kwargs):
        for k,v in kwargs.iteritems():
            try:
                setattr(self, "_%s" % k, v)
            except: pass
        
        self.__allkwargs__ = copy.copy(kwargs)
        kwargs.pop("widget", None)
        self.__kwargs__ = kwargs
    
    def render(self, *args, **kwargs):
        try:
            ren = self._object.render(*args, **kwargs)
            try:
                return "".join(ren)
            except Exception as e:
                return ren
        except:
            pass


class FormElement(Widget):
    _fields = []
    _id = ""
    _name = ""
    _cls = ""

    def __init__(self, *args, **kwargs):
        super(FormElement, self).__init__(*args, **kwargs)
        if not self._object is None:
            for k,v in self.__class__._getfields().iteritems():
                if isinstance(v, FormField):
                    n_obj = v.__class__(**v.__allkwargs__)
                    obj = self._object.__dict__[k]
                    obj._widget = n_obj._widget if n_obj._widget else obj._widget
                    n_obj._object = obj
                    self.__dict__[k] = n_obj

    @classmethod
    def _getfields(cls):
        fields = {}
        for k,v in cls.__dict__.iteritems():
            if isinstance(v, FormField): fields[k]=v

        for i in cls.__bases__:
            try:
                fields.update(i._getfields())
            except:pass
        return fields

    def render_fields(self, namespace=None):
        parts = []
        all_fields = self.__class__._getfields()
        for fi in self._fields:
            try:
                i = all_fields[fi]
                name = fi
                widget = i._widget
                obj = self._object.__dict__.get(name, None)
                ns = "-".join([namespace, name]) if namespace else name
                parts.extend(self.render_child(obj, widget, ns, **i.__kwargs__))
            except Exception as e: 
                print e
                pass
        
        return parts

    def render_label(self, name, label):
        return "<label for='%s'>%s</label>" % (name, label)

    def render_child(self, obj, widget, namespace, **kwargs):
        if widget:
            if isinstance(obj, Field):
                label = kwargs.get("label", None)
                a = [self.render_label(namespace, label)] if label else []
                a.append(obj.render(widget=widget, namespace=namespace, **kwargs))
                return a
            else:
                return obj.render(widget=widget, namespace=namespace, **kwargs)

        else:
            if isinstance(obj, Field):
                label = kwargs.get("label", None)
                a = [self.render_label(namespace, label)] if label else []
                a.append(obj.render(namespace=namespace, **kwargs))
                return a
            else:
                return obj.render(namespace=namespace, **kwargs)
    
    def __iter__(self):
        for fi in self._fields:
            v = self.__dict__[fi]
            yield v
    


class FieldSet(FormElement):

    def render(self, *args, **kwargs):
        for k,v in kwargs.iteritems():
            try:
                setattr(self, "_%s"%k, v)
            except: pass

        parts = []
        ns = kwargs.get('namespace')
        st = "<fieldset id='%(id)s' name='%(name)s' class='%(cls)s'>"
        vals ={
            "id":self._id,
            "name": ns,
            "cls":self._cls
        }
        parts.append(st % vals)
        parts.extend(self.render_fields(namespace=ns))
        parts.append("</fieldset>")
        return parts


class Form(FormElement):
    #Attributes
    _action = ""
    _method = "POST"
    _type = "multipart/form"
    _data = None
    errors = {}
        
    def render(self):
        parts = []
        st = "<form id='%(id)s' class='%(cls)s' name='%(name)s' action='%(action)s' method='%(method)s' type='%(type)s'>"
        vals = {
            "id":self._id,
            "cls": self._cls,
            "name":self._name,
            "action":self._action,
            "method":self._method,
            "type":self._type
        }
        parts.append(st % vals)
        parts.extend(self.render_fields())
        parts.append(self.submit())
        parts.append("</form>")
        return "".join(parts)

    def parse_data(self, data):
        obj = {}
        for k,v in data.iteritems():
            parts = k.split('-')
            branch = obj
            for part in parts[0:-1]:
                branch = branch.setdefault(part, {})
        
            branch[parts[-1]] = v
        
        return obj

    def validate(self):
        if self._data: 
            obj = self.parse_data(self._data)
            self._object._map(obj)
            errors = self._object._errors()
            if len(errors.keys()): 
                self.errors = errors
                raise DocumentException(errors=errors)


    def submit(self):
        return "<input type='submit' value='submit' />"