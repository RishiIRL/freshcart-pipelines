import pandas as pd

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
def transform(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
    """Check input data quality:
    1. No missing values in any column.
    2. Exactly 3 unique classes in the target column.
    3. All feature columns are numeric.
    Returns the input dataframe unchanged so the pipeline can continue.
    """
    expected_features = [
        'sepal length (cm)',
        'sepal width (cm)',
        'petal length (cm)',
        'petal width (cm)',
    ]
    for col in expected_features:
        if col not in df.columns:
            raise ValueError(f'Missing expected feature column: {col}')
        if df[col].isnull().any():
            raise ValueError(f'Missing values found in feature column: {col}')
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f'Feature column {col} must be numeric')

    if 'target' not in df.columns:
        raise ValueError('Missing target column')
    n_classes = df['target'].nunique()
    if n_classes != 3:
        raise ValueError(f'Expected exactly 3 classes in target, got {n_classes}')

    print(f'[validate_iris] OK: {len(df)} rows, 0 missing values, {n_classes} classes')
    return df


@test
def test_output(output, *args, **kwargs):
    assert output is not None, 'The output is undefined'
    assert len(output) == 150, 'Output should have 150 rows'
    assert output['target'].nunique() == 3, 'Output should have exactly 3 classes'
    assert not output.isnull().any().any(), 'Output should have no missing values'
