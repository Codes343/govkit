import httpx
import pytest
import respx

from govkit.http import GovKitClient, UpstreamError
from govkit.sources import federal_register as fr
from govkit.sources import grants_gov


def _envelope(hits, hit_count=None):
    return {
        "errorcode": 0,
        "msg": "Webservice Succeeds",
        "data": {
            "hitCount": hit_count if hit_count is not None else len(hits),
            "oppHits": hits,
        },
    }


def _hit(n):
    return {
        "id": str(n),
        "number": f"OPP-{n}",
        "title": f"Grant &amp; Study {n}",
        "agencyCode": "NSF",
        "agency": "U.S. National Science Foundation",
        "oppStatus": "posted",
        "docType": "synopsis",
        "openDate": "09/19/2019",
        "closeDate": "08/05/2026",
        "cfdaList": ["47.075"],
    }


# --- grants.gov -----------------------------------------------------------


def test_normalize_hit_cleans_entities_dates_and_builds_a_url():
    out = grants_gov.normalize_hit(_hit(320753))
    assert out["title"] == "Grant & Study 320753"
    assert out["postedDate"] == "2019-09-19"
    assert out["closeDate"] == "2026-08-05"
    assert out["url"] == "https://grants.gov/search-results-detail/320753"
    assert out["alnNumbers"] == ["47.075"]


def test_normalize_detail_coerces_the_none_string_and_flattens_lookups():
    detail = grants_gov.normalize_detail(
        {
            "opportunityCategory": {"category": "D", "description": "Discretionary"},
            "synopsis": {
                "awardCeiling": "none",  # the string, not null
                "awardFloor": "550",
                "costSharing": False,
                "applicantTypes": [{"id": "99", "description": "Unrestricted"}],
                "fundingInstruments": [{"id": "G", "description": "Grant"}],
                "responseDateStr": "2026-08-05-00-00-00",
                "synopsisDesc": "Supports <b>research</b> &mdash; broadly.",
            },
        }
    )
    assert "awardCeiling" not in detail
    assert detail["awardFloor"] == 550.0
    assert detail["costSharingRequired"] is False
    assert detail["eligibleApplicants"] == ["Unrestricted"]
    assert detail["fundingInstruments"] == ["Grant"]
    assert detail["responseDate"] == "2026-08-05"
    assert detail["description"] == "Supports research — broadly."
    assert detail["opportunityCategory"] == "Discretionary"


def test_build_search_body_pipe_delimits_arrays():
    body = grants_gov.build_search_body(
        keyword="ai", statuses=["posted", "forecasted"], agencies=["NSF", "DOE"]
    )
    assert body["oppStatuses"] == "posted|forecasted"
    assert body["agencies"] == "NSF|DOE"
    assert body["keyword"] == "ai"


@respx.mock
async def test_search_raises_on_logical_error_hidden_behind_http_200():
    """Grants.gov signals failure with errorcode, not status code."""
    respx.post(grants_gov.SEARCH_URL).mock(
        return_value=httpx.Response(200, json={"errorcode": 1, "msg": "Bad request"})
    )
    async with GovKitClient("grants.gov", min_interval=0) as client:
        with pytest.raises(UpstreamError, match="Bad request"):
            async for _ in grants_gov.search(client, max_items=10):
                pass


@respx.mock
async def test_search_paginates_and_respects_max_items():
    respx.post(grants_gov.SEARCH_URL).mock(
        side_effect=[
            httpx.Response(200, json=_envelope([_hit(n) for n in range(100)], 250)),
            httpx.Response(200, json=_envelope([_hit(n) for n in range(100, 150)], 250)),
        ]
    )
    async with GovKitClient("grants.gov", min_interval=0) as client:
        total = 0
        async for page in grants_gov.search(client, max_items=150):
            total += len(page)
    assert total == 150


@respx.mock
async def test_search_stops_when_a_page_comes_back_empty():
    respx.post(grants_gov.SEARCH_URL).mock(
        return_value=httpx.Response(200, json=_envelope([], 0))
    )
    async with GovKitClient("grants.gov", min_interval=0) as client:
        pages = [p async for p in grants_gov.search(client, max_items=1000)]
    assert pages == []


@respx.mock
async def test_enrich_survives_a_single_bad_detail_lookup():
    respx.post(grants_gov.FETCH_URL).mock(
        side_effect=[
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(500),
        ]
    )
    records = [grants_gov.normalize_hit(_hit(1))]
    async with GovKitClient("grants.gov", max_retries=4, min_interval=0) as client:
        out = await grants_gov.enrich(client, records)

    # The base record still ships; the failure is reported, not swallowed.
    assert out[0]["opportunityId"] == "1"
    assert "detailError" in out[0]


# --- federal register -----------------------------------------------------


def test_fr_normalize_flattens_agencies_and_formats_cfr_citations():
    out = fr.normalize(
        {
            "document_number": "2026-15123",
            "title": "A Rule",
            "type": "Rule",
            "abstract": "Concerns &amp; matters",
            "publication_date": "2026-07-29",
            "agencies": [
                {"name": "Transportation Department", "raw_name": "DOT"},
                {"name": "Transportation Department", "raw_name": "DOT"},
                {"raw_name": "Federal Railroad Administration"},
            ],
            "cfr_references": [{"title": 47, "part": 1}],
            "html_url": "https://example.gov/doc",
        }
    )
    assert out["agencies"] == [
        "Transportation Department",
        "Federal Railroad Administration",
    ]
    assert out["cfrReferences"] == ["47 CFR 1"]
    assert out["abstract"] == "Concerns & matters"
    assert "effectiveDate" not in out


def test_fr_build_params_uses_bracket_conditions():
    params = fr.build_params(
        term="pfas", document_types=["RULE"], published_after="2026-01-01"
    )
    assert params["conditions[term]"] == "pfas"
    assert params["conditions[type][]"] == ["RULE"]
    assert params["conditions[publication_date][gte]"] == "2026-01-01"


@respx.mock
async def test_fr_search_follows_the_cursor_then_stops():
    page2 = "https://www.federalregister.gov/api/v1/documents?page=2"
    respx.get(fr.BASE_URL).mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"document_number": "a"}], "next_page_url": page2},
        )
    )
    respx.get(page2).mock(
        return_value=httpx.Response(
            200, json={"results": [{"document_number": "b"}], "next_page_url": None}
        )
    )
    async with GovKitClient("fr", min_interval=0) as client:
        docs = [d async for page in fr.search(client, max_items=100) for d in page]

    assert [d["documentNumber"] for d in docs] == ["a", "b"]
