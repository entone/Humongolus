import copy
from humongolus import Widget, Field, Document, EmbeddedDocument, Lazy, List, DocumentException, EMPTY

def escape(s):
    orig = copy.copy(s)
    try:
        s = unicode(s)
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
    except: return orig

class HTMLElement(Widget):
    _type = "text"
    _tag = "input"
    _fields = []


    def render_fields(self, namespace=None, **kwargs):
        parts = []
        for fi in self._fields:
            try:
                i = self.__dict__[fi]
                ns = "-".join([namespace, i.attributes._name]) if namespace else i.attributes._name
                if kwargs.get("render_labels", None):
                    label = "%s_%s" % (self.attributes.prepend, ns) if self.attributes.prepend else ns 
                    if i.attributes.label: parts.append(self.render_label(label, i.attributes.label))
                a = i.render(namespace=ns, **kwargs)
                if isinstance(a, list): parts.extend(a)
                else: parts.append(a)
            except Exception as e:
                print e
                pass
        
        return parts

    def render_label(self, name, label):
        return "<label for='%s'>%s</label>" % (name, label)

    def label_tag(self):
        return self.render_label(self.attributes.name, self.attributes.label)

    def compile_tag(self, obj, close=True):
        atts = ["<%s" % obj.pop("tag", "input")]
        obj.update(obj.pop("extra", {}))
        for k,v in obj.iteritems():
            if v in EMPTY: continue
            v = v if isinstance(v, list) else [v]
            atts.append(u"%s='%s'" % (k, u" ".join([escape(val) for val in v])))
        
        atts.append("/>" if close else ">")
        return u" ".join(atts)

    def __iter__(self):
        for fi in self._fields:
            v = self.__dict__[fi]
            yield v

class Input(HTMLElement):
    
    def render(self, *args, **kwargs):
        self._type = kwargs.get("type", self._type)
        self.attributes._name = kwargs.get("namespace", self.attributes._name)
        self.attributes._id = kwargs.get("id", "id_%s"%self.attributes._name)
        self.attributes.value = kwargs.get("value", self.object.__repr__())
        self.attributes.description = kwargs.get("description", self.attributes.description)
        self.attributes.cls = kwargs.get("cls", self.attributes.cls)
        self.attributes.label = kwargs.get("label", self.attributes.label)
        self.attributes.extra = kwargs.get("extra", self.attributes.extra)
        obj = {
            "tag":self._tag,
            "type":self._type,
            "id":self.attributes.id,
            "name":self.attributes.name,
            "value":self.attributes.value,
            "class":self.attributes.cls,
            "extra":self.attributes.extra
        }
        return self.compile_tag(obj)

class Password(Input):
    _type = "password"

class CheckBox(Input):
    _type = "checkbox"

    def render(self, *args, **kwargs):
        extra = {"checked":'CHECKED'} if self.object._value else {}
        kwargs["extra"] = extra
        kwargs["value"] = self.attributes._name
        return super(CheckBox, self).render(*args, **kwargs)

class Select(Input):

    def render(self, *args, **kwargs):
        val = super(Select, self).render(*args, **kwargs)
        obj = {
            "tag":"select",
            "id":self.attributes.id,
            "name":self.attributes.name,
            "class":self.attributes.cls,
            "extra":self.attributes.extra
        }
        st = self.compile_tag(obj, close=False)
        ch = []
        for i in self.object.get_choices(render=self.attributes.item_render):
            val = i['value'] if isinstance(i, dict) else i
            display = i['display'] if isinstance(i, dict) else i
            sel = "selected='SELECTED'" if val == self.object._value else ""
            ch.append("<option value='%s' %s>%s</option>" % (val, sel, display))
        
        return "%s%s</select>" % (st, "".join(ch))

class MultipleSelect(Input):

    def render(self, *args, **kwargs):
        val = super(MultipleSelect, self).render(*args, **kwargs)
        obj = {
            "tag":"select",
            "id":self.attributes.id,
            "name":self.attributes.name,
            "class":self.attributes.cls,
            "extra":self.attributes.extra
        }
        st = self.compile_tag(obj, close=False)
        ch = []
        for i in self.object.get_choices(render=self.attributes.item_render):
            val = i['value'] if isinstance(i, dict) else i
            display = i['display'] if isinstance(i, dict) else i
            sel = "selected='SELECTED'" if val in self.object else ""
            ch.append("<option value='%s' %s>%s</option>" % (val, sel, display))
        
        return "%s%s</select>" % (st, "".join(ch))


class TextArea(Input):

    def render(self, *args, **kwargs):
        val = super(TextArea, self).render(*args, **kwargs)
        obj = {
            "tag":"textarea",
            "id":self.attributes.id,
            "name":self.attributes.name,
            "class":self.attributes.cls,
            "cols":self.attributes.cols,
            "rows":self.attributes.rows,
            "extra":self.attributes.extra
        }
        st = self.compile_tag(obj, close=False)
        return "%s%s</textarea>" % (st, self.attributes.value if self.attributes.value else "")

    
class FieldSet(HTMLElement):

    def render(self, *args, **kwargs):
        val = super(FieldSet, self).render(*args, **kwargs)
        parts = []
        obj = {
            "tag":"fieldset",
            "id":self.attributes.id,
            "name":self.attributes.name,
            "cls":self.attributes.cls,
            "extra":self.attributes.extra
        }
        st = self.compile_tag(obj, close=False)
        ns = kwargs.pop('namespace', None)
        parts.append(st)
        parts.extend(self.render_fields(namespace=ns, **kwargs))
        parts.append("</fieldset>")
        return parts

class Form(HTMLElement):
    #Attributes
    errors = {}
        
    def render(self, *args, **kwargs):
        val = super(Form, self).render(*args, **kwargs)
        parts = []
        obj = {
            "tag":"form",
            "id":self.attributes.id,
            "name":self.attributes.name,
            "class":self.attributes.cls,
            "action":self.attributes.action,
            "method":self.attributes.method,
            "type":self.attributes.type,
            "extra":self.attributes.extra
        }
        st = self.compile_tag(obj, close=False)
        parts.append(st)
        parts.extend(self.render_fields(**kwargs))
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
            print obj
            self.object._map(obj)
            errors = self.object._errors()
            if len(errors.keys()):
                for k,v in errors.iteritems():
                    try:
                        self.__dict__[k].errors.append(v)
                    except: pass
                self.errors = errors
                raise DocumentException(errors=errors)

    def submit(self):
        return "<input type='submit' value='submit' />"