from pydynasync import attributes as A, models as M

# some simple test models:

class AttrTest(M.Model):

    required = A.Attribute()
    optional = A.Attribute(nullable=True)


class IntAttrTest(M.Model):

    required = A.IntegerAttribute()
    optional = A.IntegerAttribute(nullable=True)


class Person(M.Model):

    name_ = A.Attribute()
    nickname = A.Attribute(nullable=True)
    age = A.IntegerAttribute()
