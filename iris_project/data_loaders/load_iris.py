from sklearn.datasets import load_iris as _load_iris

if 'data_loader' not in globals():
    try:
        from mage_ai.data_preparation.decorators import data_loader
    except ImportError:
        def data_loader(func):
            return func

if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(func):
            return func


@data_loader
def load_data(*args, **kwargs):
    data = _load_iris(as_frame=True)
    return data.frame


@test
def test_output(output, *args, **kwargs):
    assert output is not None, 'The output is undefined'
    assert len(output) == 150, 'The output should have 150 rows'
