from humongolus import Widget

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
		print kwargs
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

