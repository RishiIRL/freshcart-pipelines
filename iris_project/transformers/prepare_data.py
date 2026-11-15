import pandas as pd
from sklearn.model_selection import train_test_split

if 'transformer' not in globals():
    try:
        from mage_ai.data_preparation.decorators import transformer
    except ImportError:
        def transformer(func):
            return func

if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(func):
            return func


@transformer
def transform(df, *args, **kwargs):
    train, test = train_test_split(df, test_size=0.2, random_state=42)
    train['split'] = 'train'
    test['split'] = 'test'
    return pd.concat([train, test])


@test
def test_output(output, *args, **kwargs):
    assert output is not None
