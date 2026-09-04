from pwm_ldct_recon.demo import demo_ok, run_demo


def test_run_demo_end_to_end(tmp_path):
    report = run_demo(tmp_path / "corpus", size=16, steps=2, members=2)
    assert demo_ok(report), report
    assert report["n_baseline_methods"] == 1
    # validation block is present and structurally sane.
    v = report["validation"]
    required = {"psnr_db", "ssim", "uq_spearman", "detectability",
                "paired_methods", "paired_methods_ok"}
    assert required <= set(v)
    assert -1.0 <= v["uq_spearman"] <= 1.0
    # §4 paired gate: top-level PSNR paired with detectability; reference + blur both
    # report (psnr_db, detectability) together; the blur trap is a standing member.
    assert v["paired_methods_ok"] is True
    assert "reference" in v["paired_methods"]
    assert "blur" in v["paired_methods"]
    for name, m in v["paired_methods"].items():
        assert m["psnr_db"] is not None
        det = m["detectability"]
        assert det["cnr_mean"] is not None
        assert det["cho_auc_mean"] is not None
        assert det["n_slices"] >= 1
        # declared task + observer configuration is embedded (Rung 1.1 / Rung 1.2)
        assert det["task"] == "SKE-Gaussian20HU-s2px"
        assert det["signal"]["peak_contrast_hu"] == 20.0
        assert det["observer"]["cho"]["n_channels"] == 4
