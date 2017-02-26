from . import exp
from .const import KeyType, ProjectionType, Type


specs = {
    'ProductCatalog': exp.make_table_spec(
        'ProductCatalog',
        id=('Id', Type.N),
    ),
    'Forum': exp.make_table_spec(
        'Forum',
        id=('Name', Type.S),
    ),
    'Thread': exp.make_table_spec(
        'Thread',
        id=('ForumName', Type.S),
        range=('Subject', Type.S),
    ),
    'Reply': exp.make_table_spec(
        'Reply',
        id=('Id', Type.S),
        range=('ReplyDateTime', Type.S),
        extra_attrs=[{'AttributeName': 'PostedBy', 'AttributeType': Type.S}],
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
