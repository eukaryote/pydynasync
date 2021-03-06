import types

import pytest

from pydynasync import devguide, exp
from pydynasync import models as M

from test import StringTest, IntegerTest, Person


@pytest.fixture
def str1():
    m = StringTest()
    m.required = 'required-value'
    assert StringTest._members == ('id', 'required', 'optional')
    return types.SimpleNamespace(
        model=m,
        required=m.required,
        members=('id', 'required', 'optional'),
        # members = StringTest._members
    )


@pytest.fixture
def intattr1():
    m = IntegerTest()
    m.required = 42
    M.ModelMeta.clear_changed(m)
    return types.SimpleNamespace(
        model=m,
        required=m.required,
        members=('id', 'required', 'optional'),
    )


@pytest.fixture
def person1():
    person = Person()
    person.id = 1234
    person.name_ = 'Job Bluth'
    person.age = 35
    M.ModelMeta.clear_changed(person)
    return types.SimpleNamespace(
        person=person,
        id=person.id,
        name_=person.name_,
        nickname=person.nickname,
        age=person.age,
        members=('id', 'name_', 'nickname', 'age'),
    )


@pytest.fixture
def product_catalog_spec():
    return devguide.specs['ProductCatalog']


@pytest.fixture
def forum_spec():
    return devguide.specs['Forum']


@pytest.fixture
def thread_spec():
    return devguide.specs['Thread']


@pytest.fixture
def reply_spec():
    return devguide.specs['Reply']


@pytest.fixture
def test_spec():
    return devguide.specs['Test']


@pytest.fixture
def test1_spec():
    return devguide.specs['Test1']


@pytest.fixture
def product_catalog_table(product_catalog_spec, client):
    yield exp.create_table(client, product_catalog_spec)
    client.delete_table(TableName=product_catalog_spec.TableName)


@pytest.fixture
def forum_table(forum_spec, client):
    yield exp.create_table(client, forum_spec)
    client.delete_table(TableName=forum_spec.TableName)


@pytest.fixture
def thread_table(thread_spec, client):
    yield exp.create_table(client, thread_spec)
    client.delete_table(TableName=thread_spec.TableName)


@pytest.fixture
def reply_table(reply_spec, client):
    yield exp.create_table(client, reply_spec)
    client.delete_table(TableName=reply_spec.TableName)


@pytest.fixture
def test_table(test_spec, client):
    yield exp.create_table(client, test_spec)
    client.delete_table(TableName=test_spec.TableName)


@pytest.fixture
def test1_table(test1_spec, client):
    yield exp.create_table(client, test1_spec)
    client.delete_table(TableName=test1_spec.TableName)


@pytest.fixture
def session():
    return exp.make_session()


@pytest.fixture
def client(session):
    return exp.get_client(session=session)
