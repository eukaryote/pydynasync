import collections
import weakref

NOTFOUND = object()

class Attribute:

    dirty = weakref.WeakKeyDictionary()

    def __init__(self, *, nullable=False):
        self.__nullable = nullable
        self.values = weakref.WeakKeyDictionary()
        self.original = weakref.WeakKeyDictionary()

    @property
    def nullable(self):
        return self.__nullable

    def reset(self, instance, value):
        """
        Set value for instance and use that value as the original value
        for change tracking.
        """
        self.original[instance] = value
        self._set(instance, value)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.values.get(instance)

    def __set__(self, instance, value):
        if value is None:
            if not self.nullable:
                raise TypeError(f'{self.__name} may not be null')

        if self.values.get(instance, NOTFOUND) == value:
            return

        update = getattr(
            type(type(instance))._changes,
            'unset' if value == self.original.get(instance, NOTFOUND) else 'set',
        )
        update(instance, self.__index)
        self._set(instance, value)

    def _set(self, instance, value):
        self.values[instance] = value

    def __delete__(self, instance):
        # print(f'__delete__({self}, {instance})')
        if not self.nullable:
            raise TypeError(f'{self.__name} may not be null')
        self.values.pop(instance, None)

    def __set_name__(self, owner, name):
        # print(f'__set_name__({owner}, {name})', type(name), dir(name))
        if not issubclass(owner, Model):
            msg = "model attributes may only be class attributes of a Model"
            raise TypeError(msg)
        self.__name = name
        self.__owner = owner
        indexes = type(self)._indexes
        self.__index = indexes.get(owner, 0)
        indexes[owner] = self.__index + 1

    @classmethod
    def serialize(cls, value):
        return str(value)

    @classmethod
    def deserialize(cls, value):
        return value


Attribute._indexes = weakref.WeakKeyDictionary()



class IntegerAttribute(Attribute):

    def __set__(self, instance, value):
        if not (isinstance(value, int) or (value is None and self.nullable)):
            raise TypeError(f'{value} should be an int')
        super().__set__(instance, value)


class Changes:

    def __init__(self):
        self._changes = weakref.WeakKeyDictionary()

    def _convert(self, instance, value):
        return {
            name: getattr(instance, name, None)
            for index, name in enumerate(type(instance)._members)
            if (value or 0) & (1 << index)
        } if value else {}

    def get(self, instance):
        return self._convert(instance, self._changes.get(instance, 0))

    def set(self, instance, index):
        prev = self._changes.get(instance, 0)
        self._changes[instance] = prev | (1 << index)

    def unset(self, instance, index):
        prev = self._changes.get(instance, 0)
        self._changes[instance] = prev & ~(1 << index)

    def clear(self, instance):
        self._changes[instance] = 0




class ModelMeta(type):

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        return collections.OrderedDict()

    def __new__(cls, name, bases, namespace, **kwds):
        # print(f'__new__, name={name}, bases={bases}, namespace={namespace}, '
        #       f'kwds={kwds}')
        ddb_name = kwds.pop('ddb_name', None) or name
        if kwds:
            msg = "invalid class parameter(s): " + ', '.join(kwds.keys())
            raise TypeError(msg)
        result = type.__new__(cls, name, bases, dict(namespace))
        result._members = tuple(x for x in namespace if not x.startswith('__'))
        result._ddb_name = ddb_name
        return result

    @classmethod
    def get_changed(metacls, instance):
        return metacls._changes.get(instance)

    @classmethod
    def clear_changed(metacls, instance):
        metacls._changes.clear(instance)


ModelMeta._changes = Changes()


class Model(metaclass=ModelMeta):

    def __init_subclass__(cls, **kwargs):
        # print(f'__init_subclass__({cls}, {kwargs})')
        ddb_name = kwargs.pop('ddb_name', cls.__name__)
        super().__init_subclass__(**kwargs)
        cls._ddb_name = ddb_name


class Person(Model):

    name = Attribute()
    age = IntegerAttribute()
    hair_color = Attribute()


me = Person()
me.name = 'Joseph Knecht'
me.age = 42
me.hair_color = 'brown'

other = Person()
other.name = 'Fritz Tegularius'
other.age = 29
other.hair_color = 'blonde'
