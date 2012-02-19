from humongolus import Widget, Field, Document, EmbeddedDocument, Lazy, List

class HTMLElement(Widget):
    _tag = "input"
    _type = "text"
    _name = None
    _value = None
    _classes = None
    _extra = None

class Input(HTMLElement):
    
    def render(self, *args, **kwargs):
        self._type = kwargs.get("type", self._type)
        self._name = kwargs.get("name", self._object._name)
        self._value = kwargs.get("value", self._object.__repr__())
        self._classes = kwargs.get("classes", "")
        self._extra = kwargs.get("extra", "")
        return "<%s type='%s' name='%s' value='%s' class='%s' %s />" % (self._tag, self._type, self._name, self._value, self._classes, self._extra)

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
        st = "<select name='%s' classes='%s'>" % (self._name, self._classes)
        ch = []
        for i in self._object._choices:
            val = i['value'] if isinstance(i, dict) else i
            display = i['display'] if isinstance(i, dict) else i
            ch.append("<option value='%s'>%s</option>" % (val, display))
        
        return "%s%s</select>" % (st, "".join(ch))


class FormElement(Widget):
    _cls = ""
    _id = ""
    _name = ""

    def __init__(self, *args, **kwargs):
        super(FormElement, self).__init__(*args)
        for k,v in kwargs.iteritems():
            if hasattr(self, "_%s" % k): setattr(self, "_%s" % k, v)

    def render(self, *args, **kwargs):
        for k,v in kwargs.iteritems():
            if hasattr(self, "_%s" % k): setattr(self, "_%s" % k, v)


    def render_children(self, *args, **kwargs):
        parts = []
        for k,v in self._object.__dict__.iteritems():
            if isinstance(v, (EmbeddedDocument, List)):
                if v._widget:
                    parts.extend(v.render())
                else: parts.extend(v.render(widget=FieldSet))
            elif isinstance(v, Field):
                parts.append("<label>%s</label>" % v._name)
                if v._widget:
                    parts.append(v.render())
                else: parts.append(v.render(widget=Input))
        
        return parts

class FieldSet(FormElement):

    def render(self, *args, **kwargs):
        super(FieldSet, self).render(*args, **kwargs)
        parts = []
        parts.append("<fieldset id='%(id)s' class='%(cls)s' name='%(name)s'>" % {"id":self._id, "cls":self._cls, "name":self._object._name})
        parts.append("<legend>%s</legend>" % self._object._name)
        if isinstance(self._object, List):
            for i in self._object:
                parts.extend(i.render(widget=FieldSet))
        else: parts.extend(self.render_children())
        parts.append("</fieldset>")
        return parts

class Form(FormElement):
    _action = ""
    _method = "POST"
    _type = "multipart/form"

    def render(self, *args, **kwargs):
        super(Form, self).render(*args, **kwargs)
        parts = []
        parts.append("<form id='%(id)s' class='%(cls)s' name='%(name)s' action='%(action)s' method='%(method)s' type='%(type)s'>" % {"id":self._id, "cls":self._cls, "name":self._name, "action":self._action, "method":self._method, "type":self._type})
        parts.extend(self.render_children(*args, **kwargs))
        parts.append("<input type='submit' value='submit' />")
        parts.append("</form>")
        return parts

