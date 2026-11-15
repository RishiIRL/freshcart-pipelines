import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier

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
    max_depth = kwargs.get('max_depth', 3)
    train = df[df['split'] == 'train']
    test = df[df['split'] == 'test']
    features = ['sepal length (cm)', 'sepal width (cm)', 'petal length (cm)', 'petal width (cm)']
    target = 'target'
    clf = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
    clf.fit(train[features], train[target])
    preds = clf.predict(test[features])
    out = test.copy()
    out['prediction'] = preds
    return out


@test
def test_output(output, *args, **kwargs):
    assert output is not None, 'The output is undefined'
    assert 'prediction' in output.columns, 'The output must have a prediction column'


@test
def test_accuracy(output, *args, **kwargs):
    acc = accuracy_score(output['target'], output['prediction'])
    assert acc >= 0.8, f'Accuracy {acc:.3f} is below the 0.8 threshold'
