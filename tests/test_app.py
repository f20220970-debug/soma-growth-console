import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import levers as LV
import model as M
from streamlit.testing.v1 import AppTest

APP = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.py")


def test_levers_raise_arr():
    p = M.inputs("Base")
    q, notes = LV.apply(p, ai_coverage=1.0, routing=True, review_coverage=1.0)
    assert M.run(q)[1]["arr_m24"] > M.run(p)[1]["arr_m24"] and len(notes) == 3


def test_no_levers_is_identity():
    p = M.inputs("Base")
    q, notes = LV.apply(p)
    assert q == p and notes == []


def test_app_renders_without_errors():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    labels = [m.label for m in at.metric]
    assert "ARR at month 24" in labels and "Cash runs out" in labels


def test_app_levers_change_headline():
    at = AppTest.from_file(APP, default_timeout=60).run()
    before = [m.value for m in at.metric if m.label == "ARR at month 24"][0]
    s = [x for x in at.slider if x.label.startswith("AI agent covers")][0]
    s.set_value(100).run()
    after = [m.value for m in at.metric if m.label == "ARR at month 24"][0]
    assert before != after
