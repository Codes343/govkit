"""Grants.gov — federal funding opportunities.

API: https://api.grants.gov/v1/api/search2  (POST, no authentication)
     https://api.grants.gov/v1/api/fetchOpportunity  (POST, no authentication)

Grants.gov states plainly that "authentication and authorization is not required
for search2". Everything here is US federal public-domain data.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from govkit.http import GovKitClient, UpstreamError
from govkit.normalize import (
    clean_bool,
    clean_date,
    clean_int,
    clean_money,
    clean_str,
    clean_text,
    compact,
    describe_all,
)

SOURCE = "grants.gov"
SEARCH_URL = "https://api.grants.gov/v1/api/search2"
FETCH_URL = "https://api.grants.gov/v1/api/fetchOpportunity"
DETAIL_URL_TEMPLATE = "https://grants.gov/search-results-detail/{id}"

# search2 rejects oversized pages; 100 is the largest value it reliably honours.
PAGE_SIZE = 100

VALID_STATUSES = ("forecasted", "posted", "closed", "archived")


def _check_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    """Grants.gov returns HTTP 200 even for logical errors; the truth is in errorcode."""
    if payload.get("errorcode") not in (0, "0", None):
        raise UpstreamError(SOURCE, str(payload.get("msg") or "API reported an error"))
    data = payload.get("data")
    if not isinstance(data, dict):
        raise UpstreamError(SOURCE, "response was missing its 'data' object")
    return data


def normalize_hit(hit: dict[str, Any]) -> dict[str, Any]:
    """Flatten one search2 result into a stable, documented record."""
    opp_id = clean_str(hit.get("id"))
    return compact(
        {
            "opportunityId": opp_id,
            "opportunityNumber": clean_str(hit.get("number")),
            "title": clean_text(hit.get("title")),
            "agencyCode": clean_str(hit.get("agencyCode")),
            "agencyName": clean_str(hit.get("agency")),
            "status": clean_str(hit.get("oppStatus")),
            "docType": clean_str(hit.get("docType")),
            "postedDate": clean_date(hit.get("openDate")),
            "closeDate": clean_date(hit.get("closeDate")),
            "alnNumbers": [c for c in (hit.get("cfdaList") or []) if c],
            "url": DETAIL_URL_TEMPLATE.format(id=opp_id) if opp_id else None,
            "source": SOURCE,
        }
    )


def normalize_detail(data: dict[str, Any]) -> dict[str, Any]:
    """Extract the fields worth paying for out of a fetchOpportunity payload."""
    syn = data.get("synopsis") or {}
    if not isinstance(syn, dict):
        syn = {}

    description = clean_text(syn.get("synopsisDesc"))
    return compact(
        {
            "description": description,
            "descriptionLength": len(description) if description else 0,
            "awardCeiling": clean_money(syn.get("awardCeiling")),
            "awardFloor": clean_money(syn.get("awardFloor")),
            "estimatedTotalFunding": clean_money(syn.get("estimatedFunding")),
            "expectedNumberOfAwards": clean_int(syn.get("numberOfAwards")),
            "costSharingRequired": clean_bool(syn.get("costSharing")),
            "eligibleApplicants": describe_all(syn.get("applicantTypes")),
            "fundingCategories": describe_all(syn.get("fundingActivityCategories")),
            "fundingInstruments": describe_all(syn.get("fundingInstruments")),
            "responseDate": clean_date(syn.get("responseDateStr")),
            "archiveDate": clean_date(syn.get("archiveDateStr")),
            "lastUpdatedDate": clean_date(syn.get("lastUpdatedDate")),
            "agencyContactName": clean_str(syn.get("agencyContactName")),
            "agencyContactEmail": clean_str(syn.get("agencyContactEmail")),
            "agencyContactPhone": clean_str(syn.get("agencyContactPhone")),
            "additionalInfoUrl": clean_str(syn.get("fundingDescLinkUrl")),
            "opportunityCategory": clean_str(
                (data.get("opportunityCategory") or {}).get("description")
            ),
            "version": clean_int(syn.get("version")),
        }
    )


async def _fetch_detail(client: GovKitClient, opp_id: str) -> dict[str, Any]:
    payload = await client.post_json(FETCH_URL, {"opportunityId": opp_id})
    return normalize_detail(_check_envelope(payload))


async def enrich(
    client: GovKitClient, records: list[dict[str, Any]], *, concurrency: int = 5
) -> list[dict[str, Any]]:
    """Attach full synopsis detail to a page of records.

    One bad opportunity must not sink a whole page, so failures attach a
    ``detailError`` note and the base record still ships.
    """
    sem = asyncio.Semaphore(concurrency)

    async def one(record: dict[str, Any]) -> dict[str, Any]:
        opp_id = record.get("opportunityId")
        if not opp_id:
            return record
        async with sem:
            try:
                record.update(await _fetch_detail(client, str(opp_id)))
            except UpstreamError as exc:
                record["detailError"] = str(exc)
        return record

    return await asyncio.gather(*(one(r) for r in records))


def build_search_body(
    *,
    keyword: str | None = None,
    statuses: list[str] | None = None,
    agencies: list[str] | None = None,
    eligibilities: list[str] | None = None,
    funding_categories: list[str] | None = None,
    funding_instruments: list[str] | None = None,
    aln: str | None = None,
    opportunity_number: str | None = None,
    start_record: int = 0,
    rows: int = PAGE_SIZE,
) -> dict[str, Any]:
    """search2 wants pipe-delimited strings, not arrays. Hide that from the user."""
    body: dict[str, Any] = {"rows": rows, "startRecordNum": start_record}
    if keyword:
        body["keyword"] = keyword
    if statuses:
        body["oppStatuses"] = "|".join(statuses)
    if agencies:
        body["agencies"] = "|".join(agencies)
    if eligibilities:
        body["eligibilities"] = "|".join(eligibilities)
    if funding_categories:
        body["fundingCategories"] = "|".join(funding_categories)
    if funding_instruments:
        body["fundingInstruments"] = "|".join(funding_instruments)
    if aln:
        body["cfda"] = aln
    if opportunity_number:
        body["oppNum"] = opportunity_number
    return body


async def search(
    client: GovKitClient,
    *,
    max_items: int,
    **filters: Any,
) -> AsyncIterator[list[dict[str, Any]]]:
    """Yield pages of normalized opportunities until exhausted or max_items met."""
    start = 0
    yielded = 0

    while yielded < max_items:
        rows = min(PAGE_SIZE, max_items - yielded)
        body = build_search_body(start_record=start, rows=rows, **filters)
        data = _check_envelope(await client.post_json(SEARCH_URL, body))

        hits = data.get("oppHits") or []
        if not hits:
            return

        page = [normalize_hit(h) for h in hits]
        yielded += len(page)
        start += len(hits)
        yield page

        # hitCount is the authoritative total; stop before requesting past it.
        hit_count = data.get("hitCount")
        if isinstance(hit_count, int) and start >= hit_count:
            return
        if len(hits) < rows:
            return
