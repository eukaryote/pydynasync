from . import exp
from .types import KeyType, ProjectionType, AttrType


specs = {
    'ProductCatalog': exp.make_table_spec(
        'ProductCatalog',
        id=('Id', AttrType.N),
    ),
    'Forum': exp.make_table_spec(
        'Forum',
        id=('Name', AttrType.S),
    ),
    'Thread': exp.make_table_spec(
        'Thread',
        id=('ForumName', AttrType.S),
        range=('Subject', AttrType.S),
    ),
    'Reply': exp.make_table_spec(
        'Reply',
        id=('Id', AttrType.S),
        range=('ReplyDateTime', AttrType.S),
        extra_attrs=[
            {'AttributeName': 'PostedBy', 'AttributeType': AttrType.S}
        ],
        local_secondary_indexes=[{
            'IndexName': 'PostedByIndex',
            'KeySchema': [
                {'AttributeName': 'Id', 'KeyType': KeyType.HASH},
                {'AttributeName': 'PostedBy', 'KeyType': KeyType.RANGE},
            ],
            'Projection': {
                'ProjectionType': ProjectionType.KEYS_ONLY,
            }
        }]
    ),
}
