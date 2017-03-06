import base64
import decimal

import pytest

from pydynasync import attributes as A, ddb, models as M
from pydynasync import types as T

SCALAR_ATTRIBUTE_TYPES = (
    A.String, A.Binary, A.Number, A.Integer, A.Decimal, A.Null, A.Boolean,
)
SET_ATTRIBUTE_TYPES = (
    A.StringSet, A.BinarySet, A.NumberSet, A.IntegerSet, A.DecimalSet,
)
DOCUMENT_ATTRIBUTE_TYPES = (
    A.List, A.Map,
)

ATTRIBUTE_TYPES = (SCALAR_ATTRIBUTE_TYPES + SET_ATTRIBUTE_TYPES +
                   DOCUMENT_ATTRIBUTE_TYPES)


valid_attr_values = {
    A.String: ('the', 'quick'),
    A.Binary: (b'foo', b'bar'),
    A.Number: (0, 1.1, -2, decimal.Decimal('1.1')),
    A.Integer: (0, 1, -3189, 86500),
    A.Decimal: (decimal.Decimal('0'), decimal.Decimal('1234.56')),
    A.Null: (None,),
    A.Boolean: (True, False),
    A.List: (["1", 2, decimal.Decimal('3.3')], ),
    A.Map: ({'foo': 'bar', 'baz': 'qux'}, )
}
valid_attr_values[A.StringSet] = (set(valid_attr_values[A.String]), )
valid_attr_values[A.BinarySet] = (set(valid_attr_values[A.Binary]), )
valid_attr_values[A.NumberSet] = (set(valid_attr_values[A.Number]), )
valid_attr_values[A.IntegerSet] = (set(valid_attr_values[A.Integer]), )
valid_attr_values[A.DecimalSet] = (set(valid_attr_values[A.Decimal]), )


invalid_attr_values = {
    A.String: (b'foo', b'bar'),
    A.Binary: ('the', 'quick'),
    A.Number: ('1', False, type),
    A.Integer: (1.1, decimal.Decimal('1')),
    A.Decimal: (1, '1.1'),
    A.Null: (True, False, 'None'),
    A.Boolean: (0, 1, 'true'),
}
invalid_attr_values[A.StringSet] = (set(invalid_attr_values[A.String]), )
invalid_attr_values[A.BinarySet] = (set(invalid_attr_values[A.Binary]), )
invalid_attr_values[A.NumberSet] = (set(invalid_attr_values[A.Number]), )
invalid_attr_values[A.IntegerSet] = (set(invalid_attr_values[A.Integer]), )
invalid_attr_values[A.DecimalSet] = (set(invalid_attr_values[A.Decimal]), )
invalid_attr_values[A.List] = ({1, 2, 3}, {'foo': 'bar'})
invalid_attr_values[A.Map] = (['a', 'b'], 'foobar')


# TODO: test serialization/deserialization


@pytest.fixture(params=ATTRIBUTE_TYPES)
def ModelAttr(request):
    Attr = request.param

    class MyModel(M.Model):
        id1 = A.Integer(hash_key=True)
        id2 = A.Integer(range_key=True)
        required = Attr()
        optional = Attr(nullable=True)
        ddbnamed = Attr(ddb_name='myddbnamed')

    return MyModel, Attr


def test_attribute_instanceof(ModelAttr):
    Model, Attr = ModelAttr
    assert isinstance(Model.required, Attr)
    assert isinstance(Model.optional, Attr)


def test_attribute_type(ModelAttr):
    Model, Attr = ModelAttr
    assert Model.required.type is Attr.TYPE
    assert Model.optional.type is Attr.TYPE


def test_attribute_check_valid(ModelAttr):
    Model, Attr = ModelAttr
    for value in valid_attr_values[Attr]:
        assert Model.required._check(value) == value
        assert Model.optional._check(value) == value


def test_attribute_check_invalid(ModelAttr):
    Model, Attr = ModelAttr
    for value in invalid_attr_values[Attr]:
        with pytest.raises(TypeError) as e:
            Model.required._check(value)

        if Attr.TYPE is T.AttrType.NULL:
            msg = 'expected None value '
        else:
            msg = 'expected value '
        assert str(e.value).startswith(msg)

        if value is None:
            assert Model.optional._check(None) is None
        elif Attr.TYPE is not T.AttrType.NULL:
            with pytest.raises(TypeError) as e:
                Model.optional._check(value)
            assert str(e.value).startswith('expected value')


def test_attribute_get_set(ModelAttr):
    Model, Attr = ModelAttr
    instance = Model()
    for value in valid_attr_values[Attr]:
        instance.required = value
        assert instance.required == value
        instance.optional = value
        assert instance.optional == value
        instance.ddbnamed = value
        assert instance.ddbnamed == value


def test_attribute_set_valid(ModelAttr):
    Model, Attr = ModelAttr
    instance = Model()
    for value in valid_attr_values[Attr]:
        instance.required = value
        instance.optional = value


def test_attribute_set_invalid(ModelAttr):
    Model, Attr = ModelAttr
    instance = Model()

    original_required_value = instance.required
    original_optional_value = instance.optional

    for value in invalid_attr_values[Attr]:
        with pytest.raises(TypeError) as e:
            instance.required = value
        assert str(e.value).startswith('expected ')
        assert instance.required == original_required_value

        with pytest.raises(TypeError) as e:
            instance.optional = value
        assert str(e.value).startswith('expected ')
        assert instance.optional == original_optional_value


def test_attribute_nullable(ModelAttr):
    Model, Attr = ModelAttr
    assert not Model.required.nullable
    assert Model.optional.nullable
    assert not hasattr(Model(), 'nullable')


def test_scalar_attribute_names(ModelAttr):
    Model, Attr = ModelAttr
    assert Model.required.name == 'required'
    assert Model.required.ddb_name == 'required'
    assert Model.optional.name == 'optional'
    assert Model.optional.ddb_name == 'optional'
    assert Model.ddbnamed.name == 'ddbnamed'
    assert Model.ddbnamed.ddb_name == 'myddbnamed'


def test_attribute_del_nullable(ModelAttr):
    Model, Attr = ModelAttr
    value = valid_attr_values[Attr][0]

    instance = Model()
    instance.required = value
    instance.optional = value
    assert instance.required is value
    assert instance.optional is value

    del instance.optional
    assert instance.optional is None

    with pytest.raises(TypeError) as e:
        del instance.required
    expected = "{} attribute 'required' is not nullable and may not be deleted"
    expected = expected.format(Attr.__name__)
    assert str(e.value) == expected
    assert instance.required is value


def test_attribute_name_not_reserved_word():

    # Python intercepts the ValueError and raises a RuntimeError
    with pytest.raises(RuntimeError) as e:

        class P(M.Model):
            id = A.Integer(hash_key=True)
            exists = A.String()

    cause = e.value.__cause__
    assert isinstance(cause, ValueError)

    msg = "invalid DynamoDB attribute name: 'exists' is a reserved word"
    assert str(cause) == msg


def test_number_range():

    class P(M.Model):
        id = A.Integer(hash_key=True)
        num = A.Number()

    p = P()

    with pytest.raises(ValueError) as e:
        p.num = ddb.NUMBER_RANGE[0]

    assert str(e.value).endswith('is outside permitted numeric range')

    with pytest.raises(ValueError) as e:
        p.num = ddb.NUMBER_RANGE[1]
    assert str(e.value).endswith('is outside permitted numeric range')


def test_attr_type_binary():
    data = b'The Quick Brown Fox'
    expected = {
        'Title': {'B': base64.b64encode(data)}
    }
    actual = T.AttrType.B(Title=data)
    assert expected == actual


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
