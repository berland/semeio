import os
import shutil
import json
import numpy as np
import pytest
import yaml
from res.enkf import EnKFMain, ResConfig

from semeio.jobs.scripts.correlated_observations_scaling import (
    CorrelatedObservationsScalingJob,
)
from tests.jobs.correlated_observations_scaling.conftest import TEST_DATA_DIR


def assert_obs_vector(vector, val_1, index_list=None, val_2=None):
    if index_list is None:
        index_list = []
    for node in vector:
        for index in range(len(node)):
            if index in index_list:
                assert node.getStdScaling(index) == val_2
            else:
                assert node.getStdScaling(index) == val_1


def get_job_dir():
    from semeio import jobs

    head, _ = os.path.split(os.path.abspath(jobs.__file__))
    return os.path.join(head, "config_workflow_jobs")


@pytest.mark.skipif(TEST_DATA_DIR is None, reason="no libres test-data")
@pytest.mark.usefixtures("setup_ert")
def test_old_enkf_scaling_job(setup_ert):
    res_config = setup_ert
    ert = EnKFMain(res_config)

    obs = ert.getObservations()
    obs_vector = obs["WPR_DIFF_1"]

    assert_obs_vector(obs_vector, 1.0)

    job = ert.getWorkflowList().getJob("STD_SCALE_CORRELATED_OBS")
    job.run(ert, ["WPR_DIFF_1"])

    assert_obs_vector(obs_vector, np.sqrt(4.0 / 2.0))


@pytest.mark.skipif(TEST_DATA_DIR is None, reason="no libres test-data")
@pytest.mark.usefixtures("setup_ert")
def test_installed_python_version_of_enkf_scaling_job(setup_ert, monkeypatch):
    res_config = setup_ert
    ert = EnKFMain(res_config)

    obs = ert.getObservations()
    obs_vector = obs["WPR_DIFF_1"]

    assert_obs_vector(obs_vector, 1.0)

    job_config = {"CALCULATE_KEYS": {"keys": [{"key": "WPR_DIFF_1"}]}}

    with open("job_config.yml", "w") as fout:
        yaml.dump(job_config, fout)

    ert.getWorkflowList().addJob(
        "CORRELATE_OBSERVATIONS_SCALING",
        os.path.join(get_job_dir(), "CORRELATED_OBSERVATIONS_SCALING"),
    )

    job = ert.getWorkflowList().getJob("CORRELATE_OBSERVATIONS_SCALING")
    job.run(ert, ["job_config.yml"])

    assert_obs_vector(obs_vector, np.sqrt(4.0 / 2.0))

    job_config["CALCULATE_KEYS"]["keys"][0].update({"index": [400, 800, 1200]})
    with open("job_config.yml", "w") as fout:
        yaml.dump(job_config, fout)
    job.run(ert, ["job_config.yml"])

    assert_obs_vector(
        obs_vector, np.sqrt(4.0 / 2.0), index_list=[0, 1, 2], val_2=np.sqrt(3.0 / 2.0),
    )


@pytest.mark.skipif(TEST_DATA_DIR is None, reason="no libres test-data")
@pytest.mark.usefixtures("setup_tmpdir")
def test_compare_different_jobs():
    cos_config = {"CALCULATE_KEYS": {"keys": [{"key": "WPR_DIFF_1"}]}}

    test_data_dir = os.path.join(TEST_DATA_DIR, "local", "snake_oil")

    shutil.copytree(test_data_dir, "test_data")
    os.chdir(os.path.join("test_data"))

    res_config = ResConfig("snake_oil.ert")

    ert = EnKFMain(res_config)
    obs = ert.getObservations()
    obs_vector = obs["WPR_DIFF_1"]

    assert_obs_vector(obs_vector, 1.0)

    job = ert.getWorkflowList().getJob("STD_SCALE_CORRELATED_OBS")
    job.run(ert, ["WPR_DIFF_1"])

    # Result of old job:
    assert_obs_vector(obs_vector, np.sqrt(4 / 2))

    CorrelatedObservationsScalingJob(ert).run(cos_config)

    # Result of new job with no sub-indexing:
    assert_obs_vector(obs_vector, np.sqrt(4 / 2))


@pytest.mark.skipif(TEST_DATA_DIR is None, reason="no libres test-data")
@pytest.mark.usefixtures("setup_tmpdir")
def test_main_entry_point_gen_data():
    cos_config = {
        "CALCULATE_KEYS": {"keys": [{"key": "WPR_DIFF_1"}]},
        "UPDATE_KEYS": {"keys": [{"key": "WPR_DIFF_1", "index": [400, 800]}]},
    }

    test_data_dir = os.path.join(TEST_DATA_DIR, "local", "snake_oil")

    shutil.copytree(test_data_dir, "test_data")
    os.chdir(os.path.join("test_data"))

    res_config = ResConfig("snake_oil.ert")

    ert = EnKFMain(res_config)

    CorrelatedObservationsScalingJob(ert).run(cos_config)

    obs = ert.getObservations()
    obs_vector = obs["WPR_DIFF_1"]

    assert_obs_vector(obs_vector, 1.0, [0, 1], np.sqrt(4 / 2))

    cos_config["CALCULATE_KEYS"]["keys"][0].update({"index": [400, 800, 1200]})

    CorrelatedObservationsScalingJob(ert).run(cos_config)
    assert_obs_vector(
        obs_vector, 1.0, [0, 1], np.sqrt(3.0 / 2.0),
    )

    svd_file = (
        "storage/snake_oil/ensemble/reports/CorrelatedObservationsScalingJob/svd.json"
    )
    # Assert that data was published correctly
    with open(svd_file) as f:
        reported_svd = json.load(f)
        assert reported_svd == pytest.approx(
            (6.531760256452532, 2.0045135017540487, 1.1768827000026516,), 0.1
        )

    scale_file = (
        "storage/snake_oil/ensemble/reports/"
        "CorrelatedObservationsScalingJob/scale_factor.json"
    )
    with open(scale_file) as f:
        reported_scalefactor = json.load(f)
        assert reported_scalefactor == pytest.approx(1.224744871391589, 0.1)


@pytest.mark.skipif(TEST_DATA_DIR is None, reason="no libres test-data")
@pytest.mark.usefixtures("setup_tmpdir")
def test_main_entry_point_summary_data_calc():
    cos_config = {
        "CALCULATE_KEYS": {"keys": [{"key": "WOPR_OP1_108"}, {"key": "WOPR_OP1_144"}]}
    }

    test_data_dir = os.path.join(TEST_DATA_DIR, "local", "snake_oil")

    shutil.copytree(test_data_dir, "test_data")
    os.chdir(os.path.join("test_data"))

    res_config = ResConfig("snake_oil.ert")

    ert = EnKFMain(res_config)
    obs = ert.getObservations()

    obs_vector = obs["WOPR_OP1_108"]

    for index, node in enumerate(obs_vector):
        assert node.getStdScaling(index) == 1.0

    CorrelatedObservationsScalingJob(ert).run(cos_config)

    for index, node in enumerate(obs_vector):
        assert node.getStdScaling(index) == np.sqrt(1.0)


@pytest.mark.skipif(TEST_DATA_DIR is None, reason="no libres test-data")
@pytest.mark.equinor_test
@pytest.mark.usefixtures("setup_tmpdir")
def test_main_entry_point_summary_data_update():
    cos_config = {
        "CALCULATE_KEYS": {"keys": [{"key": "WWCT:OP_1"}, {"key": "WWCT:OP_2"}]},
        "UPDATE_KEYS": {"keys": [{"key": "WWCT:OP_2", "index": [1, 2, 3, 4, 5]}]},
    }

    test_data_dir = os.path.join(TEST_DATA_DIR, "Equinor", "config", "obs_testing")

    shutil.copytree(test_data_dir, "test_data")
    os.chdir(os.path.join("test_data"))

    res_config = ResConfig("config")
    ert = EnKFMain(res_config)
    obs = ert.getObservations()
    obs_vector = obs["WWCT:OP_2"]

    CorrelatedObservationsScalingJob(ert).run(cos_config)

    for index, node in enumerate(obs_vector):
        if index in cos_config["UPDATE_KEYS"]["keys"][0]["index"]:
            assert node.getStdScaling(index) == np.sqrt(61.0 * 2.0)
        else:
            assert node.getStdScaling(index) == 1.0

    obs_vector = obs["WWCT:OP_1"]

    CorrelatedObservationsScalingJob(ert).run(cos_config)

    for index, node in enumerate(obs_vector):
        assert node.getStdScaling(index) == 1.0


@pytest.mark.skipif(TEST_DATA_DIR is None, reason="no libres test-data")
@pytest.mark.equinor_test
@pytest.mark.usefixtures("setup_tmpdir")
def test_main_entry_point_block_data_calc():
    cos_config = {"CALCULATE_KEYS": {"keys": [{"key": "RFT3"}]}}

    test_data_dir = os.path.join(TEST_DATA_DIR, "Equinor", "config", "with_RFT")

    shutil.copytree(test_data_dir, "test_data")
    os.chdir(os.path.join("test_data"))

    res_config = ResConfig("config")
    ert = EnKFMain(res_config)
    obs = ert.getObservations()

    obs_vector = obs["RFT3"]

    for index, node in enumerate(obs_vector):
        assert node.getStdScaling(index) == 1.0

    CorrelatedObservationsScalingJob(ert).run(cos_config)

    for index, node in enumerate(obs_vector):
        assert node.getStdScaling(index) == 2.0


@pytest.mark.skipif(TEST_DATA_DIR is None, reason="no libres test-data")
@pytest.mark.equinor_test
@pytest.mark.usefixtures("setup_tmpdir")
def test_main_entry_point_block_and_summary_data_calc():
    cos_config = {"CALCULATE_KEYS": {"keys": [{"key": "FOPT"}, {"key": "RFT3"}]}}

    test_data_dir = os.path.join(TEST_DATA_DIR, "Equinor", "config", "with_RFT")

    shutil.copytree(test_data_dir, "test_data")
    os.chdir(os.path.join("test_data"))

    res_config = ResConfig("config")
    ert = EnKFMain(res_config)
    obs = ert.getObservations()

    obs_vector = obs["RFT3"]

    for index, node in enumerate(obs_vector):
        assert node.getStdScaling(index) == 1.0

    CorrelatedObservationsScalingJob(ert).run(cos_config)

    for index, node in enumerate(obs_vector):
        assert node.getStdScaling(index) == np.sqrt(64)
