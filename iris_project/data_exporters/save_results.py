import pandas as pd
import os

if 'data_exporter' not in globals():
    try:
        from mage_ai.data_preparation.decorators import data_exporter
    except ImportError:
        def data_exporter(func):
            return func


@data_exporter
def export_data(df, *args, **kwargs):
    # Mage executes block code via exec() so __file__ is not defined;
    # resolve the repo root from the current working directory instead.
    out_path = os.path.abspath(os.path.join(os.getcwd(), 'iris_predictions.csv'))
    df.to_csv(out_path, index=False)
    print(f'Predictions exported to {out_path}')
