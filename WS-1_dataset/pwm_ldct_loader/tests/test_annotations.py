from pwm_ldct_loader.annotations import _iou, consolidate_readers


def test_iou_basic():
    assert _iou([0, 0, 2, 2], [0, 0, 2, 2]) == 1.0
    assert _iou([0, 0, 2, 2], [10, 10, 12, 12]) == 0.0


def test_majority_vote_includes_agreed_nodule():
    per_reader = {
        "r1": [{"slice_index": 5, "bbox_xyxy": [10, 10, 20, 20], "diameter_mm": 8.0, "texture": 4}],
        "r2": [{"slice_index": 5, "bbox_xyxy": [11, 11, 21, 21], "diameter_mm": 9.0, "texture": 4}],
        "r3": [{"slice_index": 5, "bbox_xyxy": [10, 10, 19, 19], "diameter_mm": 7.0, "texture": 5}],
    }
    out = consolidate_readers(per_reader, iou_thr=0.3, min_fraction=0.5)
    assert len(out) == 1
    nod = out[0]
    assert nod["ground_truth"] == "majority_vote"
    assert nod["n_contributing_readers"] == 3
    assert nod["diameter_mm"] == 8.0          # median of 7,8,9
    assert nod["texture"] == 4                 # median of 4,4,5


def test_minority_nodule_excluded():
    per_reader = {
        "r1": [{"slice_index": 1, "bbox_xyxy": [0, 0, 5, 5], "diameter_mm": 3.0, "texture": 2}],
        "r2": [],
        "r3": [],
    }
    out = consolidate_readers(per_reader, iou_thr=0.3, min_fraction=0.5)
    assert out == []
