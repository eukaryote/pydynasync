from pydynasync import attributes as A, models as M


class Person(M.Model):

    id = A.Integer(hash_key=True)
    name_ = A.String()
    nickname = A.String(nullable=True)
    age = A.Integer()


# test models for each type of attribute

class BinaryTest(M.Model):

    id = A.Integer(hash_key=True)
    required = A.Binary()
    optional = A.Binary(nullable=True)


"""
class BinarySetTest(M.Model):

    id = A.Number(hash_key=True)
    required = A.BinarySet()
    optional = A.BinarySet(nullable=True)
"""


class BooleanTest(M.Model):

    id = A.Integer(hash_key=True)
    required = A.Boolean()
    optional = A.Boolean(nullable=True)


class DecimalTest(M.Model):

    id = A.Integer(hash_key=True)
    required = A.Decimal()
    optional = A.Decimal(nullable=True)


class IntegerTest(M.Model):

    id = A.Integer(hash_key=True)
    required = A.Integer()
    optional = A.Integer(nullable=True)


class NullTest(M.Model):

    id = A.Integer(hash_key=True)
    required = A.Null()
    optional = A.Null(nullable=True)


class NumberTest(M.Model):

    id = A.Integer(hash_key=True)
    required = A.Number()
    optional = A.Number(nullable=True)


"""
class NumberSetTest(M.Model):

    id = A.Integer(hash_key=True)
    required = A.NumberSet()
    optional = A.NumberSet(nullable=True)
"""


class StringTest(M.Model):

    id = A.Integer(hash_key=True)
    required = A.String()
    optional = A.String(nullable=True)


class StringSetTest(M.Model):

    id = A.Integer(hash_key=True)
    required = A.StringSet()
    optional = A.StringSet(nullable=True)
