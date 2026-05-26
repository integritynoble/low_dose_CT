from pwm_ldct_loader import SCHEMA_VERSION, schema


def test_version():
    assert SCHEMA_VERSION == "0.5.0"


def test_sources():
    assert schema.SOURCES == ("lidc", "aapm", "mayo")


def test_split_fractions_sum_to_one():
    assert abs(sum(schema.SPLIT_FRACTIONS.values()) - 1.0) < 1e-9


def test_sim_path_formatting():
    assert schema.h5_ld_sim(0.25) == "recon/low_dose_sim/r025"
    assert schema.h5_ld_sim(0.10) == "recon/low_dose_sim/r010"
    assert schema.h5_ld_sim(0.50) == "recon/low_dose_sim/r050"


def test_sample_keys_are_the_contract():
    assert set(schema.SAMPLE_KEYS) == {
        "full_dose", "low_dose", "low_dose_kind", "dose_ratio", "sinogram",
        "source", "patient_id", "series_id", "slice_index", "annotations", "metadata",
    }
