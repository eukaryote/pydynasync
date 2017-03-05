from pydynasync import attributes as A, models as M


class Person(M.Model):

    name_ = A.String()
    nickname = A.String(nullable=True)
    age = A.Integer()


# test models for each type of attribute

class BinaryTest(M.Model):

    required = A.Binary()
    optional = A.Binary(nullable=True)


"""
class BinarySetTest(M.Model):

    required = A.BinarySet()
    optional = A.BinarySet(nullable=True)
"""


class BooleanTest(M.Model):

    required = A.Boolean()
    optional = A.Boolean(nullable=True)


class DecimalTest(M.Model):

    required = A.Decimal()
    optional = A.Decimal(nullable=True)


class IntegerTest(M.Model):

    required = A.Integer()
    optional = A.Integer(nullable=True)


class NullTest(M.Model):

    required = A.Null()
    optional = A.Null(nullable=True)


class NumberTest(M.Model):

    required = A.Number()
    optional = A.Number(nullable=True)


class StringTest(M.Model):

    required = A.String()
    optional = A.String(nullable=True)


class StringSetTest(M.Model):

    required = A.StringSet()
    optional = A.StringSet(nullable=True)
