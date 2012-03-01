import copy
from humongolus import Widget, Field, Document, EmbeddedDocument, Lazy, List, DocumentException

class HTMLElement(Widget):
    _tag = "input"
    _type = "text"
    _fields = []
    _label = None
    _description = None
    _value = None
    _cls = ""
    _extra = None
    _id = ""

    def get_name(self):
        return "%s_%s" % (self._prepend, self._name) if self._prepend else self._name

    def get_id(self):
        return "%s_%s" % (self._prepend, self._id) if self._prepend else self._id

    def render_fields(self, namespace=None):
        parts = []
        for fi in self._fields:
            try:
                i = self.__dict__[fi]
                ns = "-".join([namespace, i._name]) if namespace else i._name
                label = "%s_%s" % (self._prepend, ns) if self._prepend else ns 
                if i._label: parts.append(self.render_label(label, i._label))
                a = i.render(namespace=ns)
                if isinstance(a, list): parts.extend(a)
                else: parts.append(a)
            except Exception as e:
                pass
        
        return parts

    def render_label(self, name, label):
        return "<label for='%s'>%s</label>" % (name, label)
    
    def label(self):
        return self.render_label(self._name, self._label)
    
    def __getattr__(self, key):
        try:
            return self.__dict__["_%s" % key]
        except:
            raise AttributeError("%s" % key)

    def __iter__(self):
        for fi in self._fields:
            v = self.__dict__[fi]
            yield v

class Input(HTMLElement):
    
    def render(self, *args, **kwargs):
        self._type = kwargs.get("type", self._type)
        self._name = kwargs.get("namespace", self._name)
        self._value = kwargs.get("value", self._object.__repr__())
        self._description = kwargs.get("description", self._description)
        self._id = kwargs.get("id", "id_%s"%self._name)
        self._cls = kwargs.get("cls", "")
        self._label = kwargs.get("label", "")
        self._extra = kwargs.get("extra", "")
        val = self._value if self._value else ""
        return "<%s type='%s' id='%s' name='%s' value='%s' class='%s' %s />" % (self._tag, self._type, self.get_id(), self.get_name(), val, self._cls, self._extra)

class Password(Input):
    _type = "password"

class CheckBox(Input):
    _type = "checkbox"

    def render(self, *args, **kwargs):
        extra = "checked='CHECKED'" if self._object._value else ""
        kwargs["extra"] = extra
        kwargs["value"] = self._name
        return super(CheckBox, self).render(*args, **kwargs)

class Select(Input):
    _render = None

    def render(self, *args, **kwargs):
        val = super(Select, self).render(*args, **kwargs)
        st = "<select id='%s' name='%s' class='%s'>" % (self.get_id(), self.get_name(), self._cls)
        ch = []
        for i in self._object.get_choices(render=self._render):
            val = i['value'] if isinstance(i, dict) else i
            display = i['display'] if isinstance(i, dict) else i
            sel = "selected='SELECTED'" if val == self._object._value else ""
            ch.append("<option value='%s' %s>%s</option>" % (val, sel, display))
        
        return "%s%s</select>" % (st, "".join(ch))

class MultipleSelect(Input):

    def render(self, *args, **kwargs):
        val = super(MultipleSelect, self).render(*args, **kwargs)
        st = "<select id='%s' name='%s' class='%s' multiple='multiple'>" % (self.get_id(), self.get_name(), self._cls)
        ch = []
        for i in self._object.get_choices(render=self._render):
            val = i['value'] if isinstance(i, dict) else i
            display = i['display'] if isinstance(i, dict) else i
            sel = "selected='SELECTED'" if val in self._object else ""
            ch.append("<option value='%s' %s>%s</option>" % (val, sel, display))
        
        return "%s%s</select>" % (st, "".join(ch))

    
class FieldSet(HTMLElement):

    def render(self, *args, **kwargs):
        val = super(FieldSet, self).render(*args, **kwargs)
        parts = []
        st = "<fieldset id='%(id)s' name='%(name)s' class='%(cls)s'>"
        vals ={
            "id":self.get_id(),
            "name": self.get_name(),
            "cls":self._cls
        }
        ns = kwargs.get('namespace')
        parts.append(st % vals)
        parts.extend(self.render_fields(namespace=ns))
        parts.append("</fieldset>")
        return parts

class Form(HTMLElement):
    #Attributes
    _action = ""
    _method = "POST"
    _type = "multipart/form"
    _data = None
    errors = {}
        
    def render(self, *args, **kwargs):
        val = super(Form, self).render(*args, **kwargs)
        parts = []
        st = "<form id='%(id)s' class='%(cls)s' name='%(name)s' action='%(action)s' method='%(method)s' type='%(type)s'>"
        vals = {
            "id":self.get_id(),
            "cls": self._cls,
            "name":self.get_name(),
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
            key = k[len(self._prepend)+1:] if self._prepend else k
            parts = key.split('-')
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
                for k,v in errors.iteritems():
                    self.__dict__[k].errors.append(v)
                self.errors = errors
                raise DocumentException(errors=errors)

    def submit(self):
        return "<input type='submit' value='submit' />"