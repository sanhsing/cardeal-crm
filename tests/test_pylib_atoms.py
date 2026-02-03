import pytest

from pylib.atoms.time_utils import isoformat, from_iso
from pylib.atoms.format_utils import human_number, safe_str
from pylib.atoms.validate_utils import is_non_empty_str, require_keys, in_choices
from pylib.atoms.id_utils import short_id
from pylib.atoms.safe_exec import safe_call

def test_time_iso_roundtrip():
    s = isoformat()
    dt = from_iso(s)
    assert dt is not None

def test_human_number():
    assert human_number(999) == "999"
    assert human_number(1200).endswith("K")
    assert human_number(1_500_000).endswith("M")

def test_safe_str():
    assert safe_str(None) == ""
    assert safe_str(123) == "123"

def test_validate_utils():
    assert is_non_empty_str(" a ")
    assert not is_non_empty_str("  ")
    assert require_keys({"a":1,"b":2}, ["a","b"])
    assert in_choices("x", ["x","y"])

def test_short_id():
    sid = short_id(10)
    assert isinstance(sid, str) and len(sid) == 10

def test_safe_call():
    assert safe_call(lambda: 1, default=0) == 1
    assert safe_call(lambda: 1/0, default=0) == 0
