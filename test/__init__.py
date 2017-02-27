from pydynasync import attributes as A, models as M

# some simple test models:

class AttrTest(M.Model):

    required = A.Attribute()
    optional = A.Attribute(nullable=True)


class NumTest(M.Model):

    required = A.Number()
    optional = A.Number(nullable=True)


class IntTest(M.Model):

    required = A.Integer()
    optional = A.Integer(nullable=True)


class DecTest(M.Model):

    required = A.Decimal()
    optional = A.Decimal(nullable=True)


class BoolTest(M.Model):

    required = A.Boolean()
    optional = A.Boolean(nullable=True)


class Person(M.Model):

    name_ = A.Attribute()
    nickname = A.Attribute(nullable=True)
    age = A.Integer()
