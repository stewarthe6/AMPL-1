import atomsci.ddm.pipeline.compare_models as cm
from atomsci.ddm.pipeline.compare_models import nan
import sys
import os
import shutil
import tarfile
import json
import glob
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '../delaney_Panel'))
from test_delaney_panel import init, train_and_predict

sys.path.append(os.path.join(os.path.dirname(__file__), '../dc_models'))
from test_retrain_dc_models import H1_curate

def clean():
    delaney_files = glob.glob('delaney-processed*.csv')
    for df in delaney_files:
        if os.path.exists(df):
            os.remove(df)

    if os.path.exists('result'):
        shutil.rmtree('result')

    if os.path.exists('scaled_descriptors'):
        shutil.rmtree('scaled_descriptors')

def get_tar_metadata(model_tarball):
    tarf_content = tarfile.open(model_tarball, "r")
    metadata_file = tarf_content.getmember("./model_metadata.json")
    ext_metadata = tarf_content.extractfile(metadata_file)

    meta_json = json.load(ext_metadata)
    ext_metadata.close()

    return meta_json

def confirm_perf_table(json_f, df):
    '''
    df should contain one entry for the model specified by json_f

    checks to see if the parameters extracted match what's in config
    '''
    # should only have trained one model
    assert len(df) == 1
    # the one row
    row = df.iloc[0]

    with open(json_f) as f:
        config = json.load(f)

    model_type = config['model_type']
    if model_type == 'NN':
        assert row['best_epoch'] > 0
        assert row['max_epochs'] == int(config['max_epochs'])
        assert row['learning_rate'] == float(config['learning_rate'])
        assert row['layer_sizes'] == config['layer_sizes']
        assert row['dropouts'] == config['dropouts']
    elif model_type == 'RF':
        print(row[[c for c in df.columns if c.startswith('rf_')]])
        assert row['rf_estimators'] == int(config['rf_estimators'])
        assert row['rf_max_features'] == int(config['rf_max_features'])
        assert row['rf_max_depth'] == int(config['rf_max_depth'])
    elif model_type == 'xgboost':
        print(row[[c for c in df.columns if c.startswith('xgb_')]])
        assert row['xgb_gamma'] == float(config['xgb_gamma'])
        assert row['xgb_learning_rate'] == float(config['xgb_learning_rate'])

def test_RF_results():
    init()
    json_f = 'jsons/reg_config_delaney_fit_RF_mordred_filtered.json'
    train_and_predict(json_f)

    df = cm.get_filesystem_perf_results('result', 'regression')
    confirm_perf_table(json_f, df)

    df = cm.get_summary_perf_tables(result_dir='result', prediction_type='regression')
    confirm_perf_table(json_f, df)

    model_uuid = df['model_uuid'].values[0]
    model_info = cm.get_best_perf_table(metric_type='r2_score', model_uuid=model_uuid, result_dir='result')
    print('model_info:', model_info)
    confirm_perf_table(json_f, pd.DataFrame([model_info]))

    # here's a hard coded result to compare to. Things that change run to run have been deleted
    ref = {'collection_name': None, 'model_type': 'RF', 'featurizer': 'computed_descriptors', 
    'splitter': 'scaffold',
    'bucket': 'public', 'descriptor_type': 'mordred_filtered', 'num_samples': nan, 
    'rf_estimators': 501, 'rf_max_features': 33, 'rf_max_depth': 10000, 'max_epochs': nan,
    'best_epoch': nan, 'learning_rate': nan, 'layer_sizes': nan, 'dropouts': nan, 'xgb_gamma': nan, 
    'xgb_learning_rate': nan, 'r2_score_train': 0.9868310465536477, 'rms_score_train': 0.23420071038051685, 
    'r2_score_valid': 0.6749311013819588, 'rms_score_valid': 1.0925651018717388, 
    'r2_score_test': 0.6573317661939333, 'rms_score_test': 1.2246446102121993}

    for k, v in ref.items():
        if not v  == v:
            # in the case of nan
            assert not model_info[k] == model_info[k]
        elif v is None:
            assert model_info[k] is None
        elif type(v) == str:
            assert model_info[k] == v
        else:
            # some kind of numerical object
            assert abs(model_info[k]-v) < 1e-6

    clean()

def test_NN_results():
    init()
    json_f = 'jsons/reg_config_delaney_fit_NN_graphconv.json'
    train_and_predict(json_f)

    df = cm.get_filesystem_perf_results('result', 'regression')
    confirm_perf_table(json_f, df)

    df = cm.get_summary_perf_tables(result_dir='result', prediction_type='regression')
    confirm_perf_table(json_f, df)

    clean()

def test_XGB_results():
    init()
    json_f = 'jsons/reg_config_delaney_fit_XGB_mordred_filtered.json'
    train_and_predict(json_f)

    df = cm.get_filesystem_perf_results('result', 'regression')
    confirm_perf_table(json_f, df)

    df = cm.get_summary_perf_tables(result_dir='result', prediction_type='regression')
    confirm_perf_table(json_f, df)

    clean()

if __name__ == '__main__':
    test_RF_results()
#    test_NN_results()
#    test_XGB_results()