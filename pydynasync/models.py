import collections
import weakref

NOTFOUND = object()

# Could possibly use an int as a bitflag to denote which attributes are
# dirty on a given instance (attrs number from 1..n, and set 2**x = 1)

ddb_name_to_model = {}
attribute_indexes = weakref.WeakKeyDictionary()
dirty_attributes = weakref.WeakKeyDictionary()


class Attribute:

    dirty = weakref.WeakKeyDictionary()

    def __init__(self, *, nullable=False):
        self.__nullable = nullable
        self.values = weakref.WeakKeyDictionary()

    @property
    def nullable(self):
        return self.__nullable

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.values.get(instance)

    def __set__(self, instance, value):
        global dirty_attributes
        if value is None:
            if not self.nullable:
                raise TypeError(f'{self.__name} may not be null')
        previous = self.values.get(instance, NOTFOUND)
        self.values[instance] = value
        if value != previous:
            # type(self).dirty[instance] = self.__name
            dirty = dirty_attributes.get(instance, 0)
            dirty_attributes[instance] = dirty | (1 << self.__index)

    def __delete__(self, instance):
        print(f'__delete__({self}, {instance})')
        if not self.nullable:
            raise TypeError(f'{self.__name} may not be null')
        self.values.pop(instance, None)

    def __set_name__(self, owner, name):
        print(f'__set_name__({owner}, {name})')
        self.__name = name
        self.__owner = owner
        index = attribute_indexes.get(owner, 0)
        self.__index = index
        attribute_indexes[owner] = index + 1


class IntegerAttribute(Attribute):

    def __set__(self, instance, value):
        if not (isinstance(value, int) or (value is None and self.nullable)):
            raise TypeError(f'{value} should be an int')
        super().__set__(instance, value)


class ModelMeta(type):

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        return collections.OrderedDict()

    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, dict(namespace))
        print('namespace:', namespace)
        result.members = tuple(x for x in namespace if not x.startswith('__'))
        return result

    @staticmethod
    def get_changed(instance):
        return {
            name: getattr(instance, name, None)
            for index, name in enumerate(type(instance).members)
            if dirty_attributes.get(instance, 0) & (1 << index)
        }

    @staticmethod
    def clear_changed(instance):
        dirty_attributes[instance] = 0


class Model(metaclass=ModelMeta):

    def __init_subclass__(cls, **kwargs):
        print(f'__init_subclass__({cls}, {kwargs})')
        ddb_name = kwargs.pop('ddb_name', None)
        if not ddb_name:
            ddb_name = cls.__name__
        super().__init_subclass__(**kwargs)
        ddb_name_to_model[ddb_name] = cls


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
