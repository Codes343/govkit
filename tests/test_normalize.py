from fedstack.normalize import (
    clean_bool,
    clean_date,
    clean_money,
    clean_str,
    clean_text,
    compact,
    describe_all,
)


def test_clean_str_treats_gov_nullish_strings_as_none():
    # Grants.gov really does return the string "none" for absent award amounts.
    for value in ["none", "None", "N/A", "", "  ", "-", "null"]:
        assert clean_str(value) is None
    assert clean_str("  NSF ") == "NSF"


def test_clean_money_handles_currency_formatting_and_nullish():
    assert clean_money("$1,250,000") == 1_250_000.0
    assert clean_money("550") == 550.0
    assert clean_money("none") is None
    assert clean_money("not a number") is None


def test_clean_date_parses_every_federal_spelling():
    assert clean_date("2019-09-19-00-00-00") == "2019-09-19"
    assert clean_date("09/19/2019") == "2019-09-19"
    assert clean_date("Sep 19, 2019 12:00:00 AM EDT") == "2019-09-19"
    assert clean_date("20190919") == "2019-09-19"
    assert clean_date("2019-09-19T13:45:00Z") == "2019-09-19"
    assert clean_date(None) is None


def test_clean_date_preserves_unparseable_values_rather_than_dropping_data():
    assert clean_date("sometime in the fall") == "sometime in the fall"


def test_clean_text_unescapes_entities_and_strips_markup():
    raw = "Learning &mdash; and<br>augmented&nbsp;intelligence</p><p>Second para"
    out = clean_text(raw)
    assert "&mdash;" not in out
    assert "<br>" not in out
    assert "—" in out
    assert "Second para" in out


def test_clean_text_does_not_join_words_across_tags():
    # The whole point of substituting a space for a tag instead of "".
    assert clean_text("supports<span>research") == "supports research"


def test_clean_bool_and_describe_all():
    assert clean_bool(False) is False
    assert clean_bool("Yes") is True
    assert clean_bool("maybe") is None
    assert describe_all([{"id": "G", "description": "Grant"}, {"id": "X"}]) == ["Grant"]
    assert describe_all(None) == []


def test_compact_drops_none_but_keeps_empty_lists():
    out = compact({"a": 1, "b": None, "c": [], "d": ""})
    assert out == {"a": 1, "c": [], "d": ""}
