import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from formula_engine import FormulaEngine


def test_textjoin_ignores_empty_values():
    result = FormulaEngine.evaluate('=TEXTJOIN("-"; TRUE; "A"; ""; "B"; None; "C")')
    assert result == "A-B-C"


def test_textjoin_keeps_empty_values_when_requested():
    result = FormulaEngine.evaluate('=TEXTJOIN(", "; FALSE; "A"; ""; "B")')
    assert result == "A, , B"


def test_textjoin_flattens_nested_sequences():
    result = FormulaEngine.evaluate('=TEXTJOIN(""; TRUE; SPLIT("AA BB"; " "); "CC")')
    assert result == "AABBCC"
