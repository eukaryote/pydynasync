from botocore.exceptions import ClientError

import pytest

from pydynasync import devguide, exp
from pydynasync.const import KeyType, ProjectionType, StreamViewType, Type


@pytest.fixture
def product_catalog_spec():
    return devguide.specs['ProductCatalog']


@pytest.fixture
def forum_spec():
    return devguide.specs['Forum']
    # return exp.make_table_spec(
    #     'Forum',
    #     id=('Name', Type.S),
    # )


@pytest.fixture
def thread_spec():
    return devguide.specs['Thread']
    # return exp.make_table_spec(
    #     'Thread',
    #     id=('ForumName', Type.S),
    #     range=('Subject', Type.S),
    # )


@pytest.fixture
def reply_spec():
    return devguide.specs['Reply']
    # return exp.make_table_spec(
    #     'Reply',
    #     id=('Id', Type.S),
    #     range=('ReplyDateTime', Type.S),
    #     extra_attrs=[{'AttributeName': 'PostedBy', 'AttributeType': Type.S}],
    #     local_secondary_indexes=[{
    #         'IndexName': 'PostedByIndex',
    #         'KeySchema': [
    #             {'AttributeName': 'Id', 'KeyType': KeyType.HASH},
    #             {'AttributeName': 'PostedBy', 'KeyType': KeyType.RANGE},
    #         ],
    #         'Projection': {
    #             'ProjectionType': ProjectionType.KEYS_ONLY,
    #         }
    #     }]
    # )


@pytest.fixture
def product_catalog_table(product_catalog_spec, client):
    client.delete_table(TableName=product_catalog_spec.TableName)
    yield exp.create_table(client, product_catalog_spec)
    client.delete_table(TableName=product_catalog_spec.TableName)


@pytest.fixture
def forum_table(forum_spec, client):
    client.delete_table(TableName=forum_spec.TableName)
    yield exp.create_table(client, forum_spec)
    client.delete_table(TableName=forum_spec.TableName)


@pytest.fixture
def thread_table(thread_spec, client):
    client.delete_table(TableName=thread_spec.TableName)
    yield exp.create_table(client, thread_spec)
    client.delete_table(TableName=thread_spec.TableName)


@pytest.fixture
def reply_table(reply_spec, client):
    client.delete_table(TableName=reply_spec.TableName)
    yield exp.create_table(client, reply_spec)
    client.delete_table(TableName=reply_spec.TableName)


@pytest.fixture
def session():
    return exp.make_session()


@pytest.fixture
def client(session):
    return exp.get_client(session=session)

