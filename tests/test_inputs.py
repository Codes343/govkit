from govkit import inputs


def test_as_list_accepts_arrays_and_comma_separated_strings():
    # The Console sends an array; API and MCP callers routinely send a string.
    assert inputs.as_list(["a", "b"]) == ["a", "b"]
    assert inputs.as_list("a,b") == ["a", "b"]
    assert inputs.as_list(" a , b ,, ") == ["a", "b"]
    assert inputs.as_list(("a", "b")) == ["a", "b"]


def test_as_list_collapses_every_flavour_of_empty_to_none():
    for value in (None, "", "  ", ",,", [], ["", "  "], 42):
        assert inputs.as_list(value) is None


def test_as_text_trims_and_blanks_to_none():
    assert inputs.as_text("  NSF ") == "NSF"
    assert inputs.as_text("") is None
    assert inputs.as_text("   ") is None
    assert inputs.as_text(None) is None


def test_as_int_clamps_rather_than_failing():
    """A bad maxItems must never kill a paid run."""
    kw = {"default": 1000, "minimum": 1, "maximum": 50_000}
    assert inputs.as_int(500, **kw) == 500
    assert inputs.as_int("500", **kw) == 500
    assert inputs.as_int(500.9, **kw) == 500
    assert inputs.as_int(0, **kw) == 1  # clamped up
    assert inputs.as_int(999_999, **kw) == 50_000  # clamped down
    assert inputs.as_int("banana", **kw) == 1000  # default
    assert inputs.as_int(None, **kw) == 1000
    assert inputs.as_int("", **kw) == 1000


def test_invalid_choices_reports_only_the_bad_values():
    allowed = ("posted", "closed")
    assert inputs.invalid_choices(["posted"], allowed) == []
    assert inputs.invalid_choices(["posted", "nope"], allowed) == ["nope"]
    assert inputs.invalid_choices(None, allowed) == []


def test_as_float():
    assert inputs.as_float("1000") == 1000.0
    assert inputs.as_float(2.5) == 2.5
    assert inputs.as_float("") is None
    assert inputs.as_float("banana") is None
