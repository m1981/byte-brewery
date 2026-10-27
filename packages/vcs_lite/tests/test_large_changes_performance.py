"""AT-VCS-067: regression in a real, continuously topmost window, not a withdrawn Tk fixture."""
import json
import shutil

import pytest
import measure_footprint


def test_at_vcs_067_topmost_3000_changes_remain_responsive():
    if shutil.which("footprint") is None:
        pytest.skip("footprint is macOS only")
    measured = measure_footprint.measure(changes=3000, exercise=True)
    report = json.dumps(measured, indent=2, ensure_ascii=False)
    print(report)
    assert measured["topmost"] and measured["viewable"], report
    assert measured["changes"] == 3000 and measured["history_total"] >= 4000, report
    assert measured["heartbeat_count"] > 0, report
    assert measured["interaction_s"] and max(measured["interaction_s"].values()) < 0.5, report
    assert measured["heartbeat_max_s"] < 0.5, report
    assert max(measured["operation_s"].values()) < 2, report
    assert measured["refresh_s_median"] < 2, report
    assert measured["footprint_mib_max"] <= 100, report
    assert measured["canvas_items_max"] < 500, report
    assert measured["history_detail_items_max"] < 100, report
    assert measured["git_calls_while_idle"] == 0, report
