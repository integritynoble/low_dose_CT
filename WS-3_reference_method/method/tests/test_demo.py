from pwm_ldct_recon.demo import demo_ok, run_demo


def test_run_demo_end_to_end(tmp_path):
    report = run_demo(tmp_path / "corpus", size=16, steps=2, members=2)
    assert demo_ok(report), report
    assert report["n_baseline_methods"] == 1
    # validation block is present and structurally sane.
    v = report["validation"]
    assert set(v) == {"psnr_db", "ssim", "uq_spearman"}
    assert -1.0 <= v["uq_spearman"] <= 1.0
