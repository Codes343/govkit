"""Tests for the USAspending, openFDA and ClinicalTrials sources."""

import httpx
import pytest
import respx

from govkit.http import GovKitClient, UpstreamError
from govkit.sources import clinicaltrials as ct
from govkit.sources import openfda
from govkit.sources import usaspending as us

# --- USAspending ----------------------------------------------------------


def test_award_type_groups_never_mix_families():
    """USAspending rejects a request mixing contract and grant codes."""
    contracts = set(us.AWARD_TYPE_GROUPS["contracts"])
    grants = set(us.AWARD_TYPE_GROUPS["grants"])
    assert not contracts & grants


def test_us_normalize_builds_award_url_from_generated_id():
    out = us.normalize(
        {
            "Award ID": "HT940216C0001",
            "Recipient Name": "HUMANA GOVERNMENT BUSINESS INC",
            "Award Amount": 51269205263.03,
            "Awarding Agency": "Department of Defense",
            "Start Date": "2016-08-01",
            "Award Type": None,
            "generated_internal_id": "CONT_AWD_HT940216C0001",
        }
    )
    assert out["awardAmount"] == 51269205263.03
    assert out["startDate"] == "2016-08-01"
    assert out["url"] == "https://www.usaspending.gov/award/CONT_AWD_HT940216C0001"
    assert "awardType" not in out  # null dropped, not emitted


def test_us_build_body_nests_agency_and_amount_filters():
    body = us.build_body(
        award_types=["A"],
        start_date="2025-01-01",
        end_date="2026-01-01",
        agencies=["Department of Defense"],
        award_amount_min=1000,
        place_of_performance_states=["va"],
    )
    filters = body["filters"]
    assert filters["agencies"] == [
        {"type": "awarding", "tier": "toptier", "name": "Department of Defense"}
    ]
    assert filters["award_amounts"] == [{"lower_bound": 1000}]
    assert filters["place_of_performance_locations"] == [
        {"country": "USA", "state": "VA"}
    ]
    assert body["subawards"] is False


@respx.mock
async def test_us_search_pages_until_hasnext_is_false():
    def page(n, has_next):
        return httpx.Response(
            200,
            json={
                "results": [{"Award ID": f"A{i}"} for i in range(n)],
                "page_metadata": {"hasNext": has_next},
            },
        )

    respx.post(us.SEARCH_URL).mock(side_effect=[page(100, True), page(20, False)])
    async with GovKitClient("us", min_interval=0) as client:
        total = 0
        async for batch in us.search(
            client,
            max_items=500,
            award_types=["A"],
            start_date="2025-01-01",
            end_date="2026-01-01",
        ):
            total += len(batch)
    assert total == 120


# --- openFDA --------------------------------------------------------------


def test_openfda_query_is_built_with_lucene_syntax():
    query = openfda.build_search(
        reported_after="2025-01-01",
        reported_before="2026-12-31",
        classifications=["Class I", "Class II"],
        firm="Abbott",
    )
    assert "report_date:[20250101 TO 20261231]" in query
    assert 'classification:("Class I" OR "Class II")' in query
    assert 'recalling_firm:"Abbott"' in query
    assert " AND " in query


def test_openfda_query_is_none_when_nothing_is_filtered():
    assert openfda.build_search() is None


def test_openfda_normalize_explains_the_classification():
    out = openfda.normalize(
        {"recall_number": "H-1", "classification": "Class I", "report_date": "20260318"},
        "food",
    )
    assert out["category"] == "food"
    assert out["reportDate"] == "2026-03-18"
    assert "serious health consequences" in out["classificationMeaning"]


@respx.mock
async def test_openfda_treats_404_as_no_matches_not_a_failure():
    """openFDA answers an empty result set with HTTP 404."""
    respx.get(openfda.BASE_URL.format(category="food")).mock(
        return_value=httpx.Response(404, json={"error": {"code": "NOT_FOUND"}})
    )
    respx.get(openfda.BASE_URL.format(category="drug")).mock(
        return_value=httpx.Response(
            200,
            json={
                "meta": {"results": {"total": 1}},
                "results": [{"recall_number": "D-1"}],
            },
        )
    )
    async with GovKitClient("fda", min_interval=0) as client:
        rows = [
            r
            async for page in openfda.search(
                client, max_items=10, categories=["food", "drug"]
            )
            for r in page
        ]
    # The empty food category is skipped; drug results still ship.
    assert [r["recallNumber"] for r in rows] == ["D-1"]


@respx.mock
async def test_openfda_still_raises_on_a_real_server_error():
    respx.get(openfda.BASE_URL.format(category="food")).mock(
        return_value=httpx.Response(500)
    )
    async with GovKitClient("fda", max_retries=1, min_interval=0) as client:
        with pytest.raises(UpstreamError):
            async for _ in openfda.search(client, max_items=5, categories=["food"]):
                pass


# --- ClinicalTrials -------------------------------------------------------


def test_ct_normalize_flattens_the_nested_protocol_section():
    out = ct.normalize(
        {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT01", "briefTitle": "A &amp; B"},
                "statusModule": {
                    "overallStatus": "RECRUITING",
                    "startDateStruct": {"date": "2026-01"},
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Pfizer", "class": "INDUSTRY"}
                },
                "designModule": {
                    "studyType": "INTERVENTIONAL",
                    "enrollmentInfo": {"count": 64, "type": "ESTIMATED"},
                },
                "conditionsModule": {"conditions": ["Type 2 Diabetes"]},
                "contactsLocationsModule": {
                    "locations": [
                        {"country": "Japan"},
                        {"country": "Japan"},
                        {"country": "United States"},
                    ]
                },
            }
        }
    )
    assert out["nctId"] == "NCT01"
    assert out["briefTitle"] == "A & B"
    assert out["leadSponsor"] == "Pfizer"
    assert out["enrollmentCount"] == 64
    assert out["startDate"] == "2026-01"  # month-only dates survive intact
    assert out["countries"] == ["Japan", "United States"]  # deduped, order kept
    assert out["locationCount"] == 3
    assert out["url"] == "https://clinicaltrials.gov/study/NCT01"


def test_ct_build_params_joins_status_filter():
    params = ct.build_params(
        condition="diabetes", overall_status=["RECRUITING", "COMPLETED"]
    )
    assert params["query.cond"] == "diabetes"
    assert params["filter.overallStatus"] == "RECRUITING,COMPLETED"


@respx.mock
async def test_ct_search_follows_page_token_then_stops():
    respx.get(ct.BASE_URL).mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "studies": [
                        {"protocolSection": {"identificationModule": {"nctId": "N1"}}}
                    ],
                    "nextPageToken": "tok",
                },
            ),
            httpx.Response(
                200,
                json={
                    "studies": [
                        {"protocolSection": {"identificationModule": {"nctId": "N2"}}}
                    ]
                },
            ),
        ]
    )
    async with GovKitClient("ct", min_interval=0) as client:
        rows = [r async for page in ct.search(client, max_items=50) for r in page]
    assert [r["nctId"] for r in rows] == ["N1", "N2"]


def test_user_agent_keeps_the_client_token():
    """ClinicalTrials.gov 403s any User-Agent without a recognised client token."""
    from govkit import USER_AGENT

    assert "python-httpx" in USER_AGENT
    assert "GovKit" in USER_AGENT
