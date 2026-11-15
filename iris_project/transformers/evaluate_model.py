import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score

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
    y_true = df['target']
    y_pred = df['prediction']
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision_macro': precision_score(y_true, y_pred, average='macro'),
        'recall_macro': recall_score(y_true, y_pred, average='macro'),
        'f1_macro': f1_score(y_true, y_pred, average='macro'),
    }
    cm = confusion_matrix(y_true, y_pred)

    print('\n=== Model Metrics ===')
    for k, v in metrics.items():
        print(f'{k}: {v:.4f}')

    print('\n=== Confusion Matrix ===')
    labels = sorted(y_true.unique())
    cm_df = pd.DataFrame(
        cm,
        index=[f'actual_{i}' for i in labels],
        columns=[f'pred_{i}' for i in labels],
    )
    print(cm_df.to_string())

    return {'metrics': metrics, 'confusion_matrix': cm}


@test
def test_output(output, *args, **kwargs):
    assert output is not None, 'The output is undefined'
    assert 'metrics' in output and 'confusion_matrix' in output, 'Output must contain metrics and confusion_matrix'
