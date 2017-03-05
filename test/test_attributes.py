import base64
import decimal
import types

import pytest

from pydynasync import attributes as A, ddb, models as M
from pydynasync import types as T

from test import (
    BooleanTest, DecimalTest, NullTest, NumberTest
)


def test_attribute_type():

    with pytest.raises(ValueError) as e:

        class MyModel(M.Model):
            attr = A.Attribute()

    assert str(e.value).startswith("`attr_type` is required if no")

    attr_type = T.AttrType.B

    class MyModel1(M.Model):

        attr = A.Attribute(attr_type=attr_type)


    assert MyModel1.attr.type is attr_type

    class CustomAttribute(A.Attribute):

        TYPE = T.AttrType.NS

    class MyModel2(M.Model):

        attr1 = CustomAttribute()
        attr2 = CustomAttribute(attr_type=attr_type)

    assert MyModel2.attr1.type is CustomAttribute.TYPE
    assert MyModel2.attr2.type is attr_type


def test_attribute_nullable():

    class MyModel(M.Model):

        attr1 = A.Attribute(attr_type=T.AttrType.S)
        attr2 = A.Attribute(attr_type=T.AttrType.S, nullable=True)
        attr3 = A.Attribute(attr_type=T.AttrType.S, nullable=False)

    assert MyModel.attr1.nullable is False
    assert MyModel.attr2.nullable is True
    assert MyModel.attr3.nullable is False


def test_attribute_ddb_name():

    class MyModel(M.Model):

        attr1 = A.Attribute(attr_type=T.AttrType.S)
        attr2 = A.Attribute(attr_type=T.AttrType.S, ddb_name='myddbname')

    assert MyModel.attr1.ddb_name == 'attr1'
    assert MyModel.attr2.ddb_name == 'myddbname'


def test_attribute_name():

    class MyModel(M.Model):

        attr1 = A.Attribute(attr_type=T.AttrType.S)
        attr2 = A.Attribute(attr_type=T.AttrType.S, ddb_name='myddbname')

    assert MyModel.attr1.name == 'attr1'
    assert MyModel.attr2.name == 'attr2'


def test_str_get(str1):
    assert str1.model.required == str1.required


def test_str_set(str1):
    new_value = str1.model.required + 'X'
    str1.model.required = new_value
    assert str1.model.required == new_value


def test_str_del_nullable(str1):
    str1.model.optional = 'foo'
    assert str1.model.optional == 'foo'
    del str1.model.optional
    assert str1.model.optional is None


def test_str_del_not_nullable(str1):
    with pytest.raises(TypeError) as e:
        del str1.model.required
    assert str(e.value) == 'required may not be null'


@pytest.mark.parametrize('value', ['42', 'asdf'])
def test_string_serialization_required(str1, value):
    assert type(str1.model).required.serialize(value) == {
        'required': {'S': value}
    }


@pytest.mark.parametrize('value', ['42', 'asdf', None])
def test_string_serialization_optional(str1, value):
    result = type(str1.model).optional.serialize(value)
    expected = None if value is None else {
        'optional': {'S': value}
    }


# TODO: serialization/deserialization tests for all types

def test_intattr_required_get(intattr1):
    assert intattr1.model.required == intattr1.required


def test_intattr_required_set(intattr1):
    a = intattr1.model
    new_value = a.required + 1
    a.required = new_value
    assert a.required == new_value

    with pytest.raises(TypeError) as e:
        a.required = '42'
    assert str(e.value) == "value '42' should be of type: int"


def test_intattr_optional_set(intattr1):
    a = intattr1.model

    # can set to int
    assert a.optional != a.required
    a.optional = a.required
    assert a.optional == a.required

    # can set to null
    a.optional = None

    # can't set to non-int/none
    with pytest.raises(TypeError) as e:
        a.optional = '42'
    assert str(e.value) == "value '42' should be of type: int"


def test_attribute_name_not_reserved_word():

    # Python intercepts the ValueError and raises a RuntimeError
    with pytest.raises(RuntimeError) as e:

        class P(M.Model):

            exists = A.String()

    cause = e.value.__cause__
    assert isinstance(cause, ValueError)

    msg = "invalid DynamoDB attribute name: 'exists' is a reserved word"
    assert str(cause) == msg


def test_attribute_name_ddb_name():

    class P1(M.Model):

        name = A.String(ddb_name='name_')


    assert P1.name.ddb_name == 'name_'

    class P2(M.Model):

        name_ = A.String()

    assert P2.name_.ddb_name == 'name_'


def test_number_range():

    class P(M.Model):

        num = A.Number()


    p = P()

    with pytest.raises(ValueError) as e:
        p.num = ddb.NUMBER_RANGE[0]

    assert str(e.value).endswith('is outside permitted numeric range')

    with pytest.raises(ValueError) as e:
        p.num = ddb.NUMBER_RANGE[1]
    assert str(e.value).endswith('is outside permitted numeric range')


@pytest.mark.parametrize('value', [-1, 0, 1E75])
def test_number_check_required_valid(value):
    assert NumberTest.required._check(value) is value


@pytest.mark.parametrize('value', [-1, 0, 1E75, None])
def test_number_check_optional_valid(value):
    assert NumberTest.optional._check(value) is value


@pytest.mark.parametrize('value,result', [
    (1, {'required': {'N': '1'}}),
    (0, {'required': {'N': '0'}}),
    (decimal.Decimal('1.1'), {'required': {'N': '1.1'}}),

])
def test_number_serialize_required(value, result):
    assert NumberTest.required.serialize(value) == result


@pytest.mark.parametrize('value,result', [
    (1, {'required': {'N': '1'}}),
    (decimal.Decimal('2.2'), {'required': {'N': '2.2'}}),
    (0, {'required': {'N': '0'}}),
])
def test_number_deserialize_required(value, result):
    assert NumberTest.required.deserialize(result) == value


@pytest.mark.parametrize('value,result', [
    (1.1, 1.1),
    (decimal.Decimal('1.1'), decimal.Decimal('1.1'))
])
def test_decimal_check_required_value(value, result):
    assert DecimalTest.required._check(value) == result


@pytest.mark.parametrize('value,result', [
    (1.1, 1.1),
    (decimal.Decimal('1.1'), decimal.Decimal('1.1')),
    (None, None),
])
def test_decimal_check_optional_value(value, result):
    assert DecimalTest.optional._check(value) == result


@pytest.mark.parametrize('value,result', [(True, 'true'), (False, 'false')])
def test_boolean_serialization_required(value, result):
    assert BooleanTest.required.serialize(value) == result
    assert BooleanTest.required.deserialize(result) == value


@pytest.mark.parametrize('value,result', [(True, 'true'), (False, 'false')])
def test_boolean_serialization_optional(value, result):
    assert BooleanTest.optional.serialize(value) == result
    assert BooleanTest.optional.deserialize(result) == value


@pytest.mark.parametrize('value', [type, 'foo', None])
def test_boolean_check_required_wrong_types(value):
    with pytest.raises(TypeError) as e:
        BooleanTest.required._check(value)
    assert str(e.value) == f'{value} should be a bool'


@pytest.mark.parametrize('value', [True, False])
def test_boolean_check_required_valid(value):
    assert BooleanTest.required._check(value) is value


@pytest.mark.parametrize('value', [type, 'foo', 0])
def test_boolean_check_optional_wrong_types(value):
    with pytest.raises(TypeError) as e:
        BooleanTest.optional._check(value)
    assert str(e.value) == f'{value} should be a bool'


@pytest.mark.parametrize('value', [True, False, None])
def test_boolean_check_optional_valid(value):
    assert BooleanTest.optional._check(value) is value


def test_attr_type_string():
    expected = {
        'FirstName': {'S': 'Jos'},
        'LastName': {'S': 'Knecht'},
    }
    actual = T.AttrType.S(FirstName='Jos', LastName='Knecht')
    assert expected == actual
    assert T.AttrType.S() == {}


def test_attr_type_binary():
    data = b'The Quick Brown Fox'
    expected = {
        'Title': {'B': base64.b64encode(data)}
    }
    actual = T.AttrType.B(Title=data)
    assert expected == actual


def test_null_check_required_valid():
    assert NullTest.required._check(True) is True


@pytest.mark.parametrize('value', [False, None, 1, '2'])
def test_null_check_required_invalid(value):
    with pytest.raises(TypeError) as e:
        NullTest.required._check(False)
    assert 'should be True or None' in str(e.value)


@pytest.mark.parametrize('value', [True, None])
def test_null_check_optional_valid(value):
    assert NullTest.optional._check(value) is value


@pytest.mark.parametrize('value', [False, None, 1, '2'])
def test_null_check_optional_invalid(value):
    with pytest.raises(TypeError) as e:
        NullTest.optional._check(False)
    assert 'should be True or None' in str(e.value)


@pytest.mark.xfail
def test_null_serialization_required():
    assert NullTest.required.serialize(True) == {
        'required': {
            'NULL': True
        }
    }


def test_attr_type_null():
    assert T.AttrType.NULL() == {}

    assert T.AttrType.NULL(a=True) == {
        'a': {
            'NULL': True,
        }
    }

    assert T.AttrType.NULL(a=True, b=True) == {
        'a': {
            'NULL': True,
        },
        'b': {
            'NULL': True,
        },
    }


def test_stringset_serialization():
    result = T.AttrType.SS.serialize('foo', {'a', 'b'})
    result['foo']['SS'].sort()
    assert result == {
        'foo': {
            'SS': ['a', 'b']
        }
    }

    result2 = T.AttrType.SS.deserialize('foo', result)
    assert result2 == {'a', 'b'}
