from pydynasync.const import KeyType, ProjectionType, Type
import pydynasync.exp as exp


def test_product_catalog_spec(product_catalog_spec):
    spec = product_catalog_spec
    assert spec.TableName == 'ProductCatalog'
    assert len(spec.AttributeDefinitions) == 1
    assert len(spec.KeySchema) == 1
    assert spec.AttributeDefinitions[0].AttributeType == Type.N


def test_forum_spec(forum_spec):
    spec = forum_spec
    assert spec.TableName == 'Forum'
    assert len(spec.AttributeDefinitions) == 1
    assert len(spec.KeySchema) == 1
    assert spec.AttributeDefinitions[0].AttributeType == Type.S


def test_thread_spec(thread_spec):
    spec = thread_spec
    assert spec.TableName == 'Thread'
    assert len(spec.AttributeDefinitions) == 2
    assert len(spec.KeySchema) == 2
    assert spec.AttributeDefinitions[0].AttributeType == Type.S
    assert spec.AttributeDefinitions[1].AttributeType == Type.S


def test_reply_spec(reply_spec):
    spec = reply_spec
    assert spec.TableName == 'Reply'
    assert spec.AttributeDefinitions == [
        exp.Attribute('Id', Type.S),
        exp.Attribute('ReplyDateTime', Type.S),
        exp.Attribute('PostedBy', Type.S),
    ]
    assert spec.KeySchema == [
        exp.Key('Id', KeyType.HASH),
        exp.Key('ReplyDateTime', KeyType.RANGE),
    ]
    assert spec.AttributeDefinitions[0].AttributeType == Type.S
    assert spec.AttributeDefinitions[1].AttributeType == Type.S
    assert spec.LocalSecondaryIndexes
    hkey, rkey = spec.KeySchema
    assert hkey.KeyType == KeyType.HASH
    assert rkey.KeyType == KeyType.RANGE
    lsi = spec.LocalSecondaryIndexes
    assert len(lsi) == 1
    index = lsi[0]
    assert index.IndexName == 'PostedByIndex'
    assert index.KeySchema == [
        exp.Key('Id', KeyType.HASH),
        exp.Key('PostedBy', KeyType.RANGE),
    ]
    assert index.Projection == exp.Projection(
        ProjectionType=ProjectionType.KEYS_ONLY,
        NonKeyAttributes=None
    )


def test_product_catalog_table(product_catalog_table, client):
    t = product_catalog_table
    assert client.describe_table(TableName=t['TableName'])


def test_forum_table(forum_table, client):
    t = forum_table
    assert client.describe_table(TableName=t['TableName'])


def test_thread_table(thread_table, client):
    t = thread_table
    assert client.describe_table(TableName=t['TableName'])


def test_reply_table(reply_table, client):
    t = reply_table
    assert client.describe_table(TableName=t['TableName'])
