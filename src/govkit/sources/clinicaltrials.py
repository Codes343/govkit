"""ClinicalTrials.gov — registered clinical studies.

API: https://clinicaltrials.gov/api/v2/studies (GET, no auth)

The v2 API returns a deeply nested `protocolSection` of ~11 modules. Flattening
it into one row per study is the entire value this actor adds.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from govkit.http import GovKitClient
from govkit.normalize import clean_date, clean_int, clean_str, clean_text, compact

SOURCE = "clinicaltrials.gov"
BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
STUDY_URL_TEMPLATE = "https://clinicaltrials.gov/study/{nct_id}"

PAGE_SIZE = 1000  # documented maximum

OVERALL_STATUSES = (
    "NOT_YET_RECRUITING",
    "RECRUITING",
    "ENROLLING_BY_INVITATION",
    "ACTIVE_NOT_RECRUITING",
    "SUSPENDED",
    "TERMINATED",
    "COMPLETED",
    "WITHDRAWN",
    "UNKNOWN",
)


def _date(struct: object) -> str | None:
    """Dates arrive as {"date": "2009-05"} and may omit the day."""
    if not isinstance(struct, dict):
        return clean_date(struct)
    return clean_date(struct.get("date"))


def _names(items: object, key: str) -> list[str]:
    if not isinstance(items, list):
        return []
    out = []
    for item in items:
        name = clean_str(item.get(key)) if isinstance(item, dict) else clean_str(item)
        if name and name not in out:
            out.append(name)
    return out


def normalize(study: dict[str, Any]) -> dict[str, Any]:
    proto = study.get("protocolSection") or {}
    ident = proto.get("identificationModule") or {}
    status = proto.get("statusModule") or {}
    sponsor = proto.get("sponsorCollaboratorsModule") or {}
    design = proto.get("designModule") or {}
    desc = proto.get("descriptionModule") or {}
    cond = proto.get("conditionsModule") or {}
    elig = proto.get("eligibilityModule") or {}
    arms = proto.get("armsInterventionsModule") or {}
    locs = proto.get("contactsLocationsModule") or {}

    nct_id = clean_str(ident.get("nctId"))
    enrollment = design.get("enrollmentInfo") or {}
    lead = sponsor.get("leadSponsor") or {}

    locations = locs.get("locations") or []
    countries: list[str] = []
    for loc in locations if isinstance(locations, list) else []:
        country = clean_str(loc.get("country")) if isinstance(loc, dict) else None
        if country and country not in countries:
            countries.append(country)

    return compact(
        {
            "nctId": nct_id,
            "briefTitle": clean_text(ident.get("briefTitle")),
            "officialTitle": clean_text(ident.get("officialTitle")),
            "overallStatus": clean_str(status.get("overallStatus")),
            "whyStopped": clean_text(status.get("whyStopped")),
            "phases": _names(design.get("phases"), "phase"),
            "studyType": clean_str(design.get("studyType")),
            "conditions": _names(cond.get("conditions"), "condition"),
            "leadSponsor": clean_str(lead.get("name")),
            "leadSponsorClass": clean_str(lead.get("class")),
            "collaborators": _names(sponsor.get("collaborators"), "name"),
            "enrollmentCount": clean_int(enrollment.get("count")),
            "enrollmentType": clean_str(enrollment.get("type")),
            "startDate": _date(status.get("startDateStruct")),
            "primaryCompletionDate": _date(status.get("primaryCompletionDateStruct")),
            "completionDate": _date(status.get("completionDateStruct")),
            "firstPostedDate": _date(status.get("studyFirstPostDateStruct")),
            "lastUpdatedDate": _date(status.get("lastUpdatePostDateStruct")),
            "briefSummary": clean_text(desc.get("briefSummary")),
            "interventions": _names(arms.get("interventions"), "name"),
            "sex": clean_str(elig.get("sex")),
            "minimumAge": clean_str(elig.get("minimumAge")),
            "maximumAge": clean_str(elig.get("maximumAge")),
            "healthyVolunteers": elig.get("healthyVolunteers"),
            "locationCount": len(locations) if isinstance(locations, list) else None,
            "countries": countries,
            "url": STUDY_URL_TEMPLATE.format(nct_id=nct_id) if nct_id else None,
            "source": SOURCE,
        }
    )


def build_params(
    *,
    condition: str | None = None,
    intervention: str | None = None,
    term: str | None = None,
    sponsor: str | None = None,
    location: str | None = None,
    overall_status: list[str] | None = None,
    page_size: int = PAGE_SIZE,
) -> dict[str, Any]:
    params: dict[str, Any] = {"pageSize": page_size, "countTotal": "true"}
    if condition:
        params["query.cond"] = condition
    if intervention:
        params["query.intr"] = intervention
    if term:
        params["query.term"] = term
    if sponsor:
        params["query.spons"] = sponsor
    if location:
        params["query.locn"] = location
    if overall_status:
        # The API expects this filter repeated/comma-joined, not bracketed.
        params["filter.overallStatus"] = ",".join(overall_status)
    return params


async def search(
    client: GovKitClient, *, max_items: int, **filters: Any
) -> AsyncIterator[list[dict[str, Any]]]:
    """Yield pages of normalized studies, following the API's page token."""
    page_size = min(PAGE_SIZE, max_items)
    params = build_params(page_size=page_size, **filters)
    yielded = 0
    token: str | None = None

    while yielded < max_items:
        request = dict(params)
        request["pageSize"] = min(PAGE_SIZE, max_items - yielded)
        if token:
            request["pageToken"] = token

        payload = await client.get_json(BASE_URL, **request)

        studies = payload.get("studies") or []
        if not studies:
            return

        batch = [normalize(s) for s in studies]
        yielded += len(batch)
        yield batch

        token = clean_str(payload.get("nextPageToken"))
        if not token:
            return
