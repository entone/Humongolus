from pymongo import collection
from pymongo import cursor


class Cursor(cursor.Cursor):    

    def __init__(self, *args, **kwargs):
        self._class = kwargs.pop("my_class")
        self._as_dict = kwargs.pop("as_dict", None)
        super(Cursor, self).__init__(*args, **kwargs)

    def __getitem__(self, *args, **kwargs):
        obj = super(Cursor, self).__getnext__(*args, **kwargs)
        if isinstance(obj, dict): return self._class(data=obj)
        return obj

    def next(self, *args, **kwargs):
        obj = super(Cursor, self).next(*args, **kwargs)
        if self._as_dict: return obj
        return self._class(data=obj)

class Collection(collection.Collection):

    def __init__(self, my_class, *args, **kwargs):
        self._class = my_class        
        super(Collection, self).__init__(*args, **kwargs)

    def find(self, *args, **kwargs):
        self._as_dict = kwargs.pop("as_dict", None)
        super(Collection, self).find(*args, **kwargs)
        return Cursor(self, my_class=self._class, as_dict=self._as_dict, *args, **kwargs)