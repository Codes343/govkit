"""Federal Register — proposed rules, final rules, notices and presidential documents.

API: https://www.federalregister.gov/api/v1/documents.json  (GET, no authentication)

The Federal Register API caps offset pagination at a few thousand documents but
returns a ``next_page_url`` cursor on every response. Following that cursor is
the only reliable way to walk a large result set, so that is what we do.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from fedstack.http import FedstackClient
from fedstack.normalize import clean_date, clean_int, clean_str, clean_text, compact

SOURCE = "federalregister.gov"
BASE_URL = "https://www.federalregister.gov/api/v1/documents.json"

PAGE_SIZE = 1000  # documented maximum

DOCUMENT_TYPES = {
    "RULE": "Final Rule",
    "PRORULE": "Proposed Rule",
    "NOTICE": "Notice",
    "PRESDOCU": "Presidential Document",
}

FIELDS = (
    "document_number",
    "title",
    "type",
    "abstract",
    "action",
    "publication_date",
    "effective_on",
    "comments_close_on",
    "agencies",
    "docket_ids",
    "regulation_id_numbers",
    "cfr_references",
    "significant",
    "page_length",
    "html_url",
    "pdf_url",
    "json_url",
)


def _agency_names(agencies: object) -> list[str]:
    if not isinstance(agencies, list):
        return []
    names = []
    for agency in agencies:
        if isinstance(agency, dict):
            name = clean_str(agency.get("name") or agency.get("raw_name"))
            if name and name not in names:
                names.append(name)
    return names


def _cfr_refs(refs: object) -> list[str]:
    if not isinstance(refs, list):
        return []
    out = []
    for ref in refs:
        if isinstance(ref, dict):
            title, part = ref.get("title"), ref.get("part")
            if title and part:
                out.append(f"{title} CFR {part}")
        elif ref:
            out.append(str(ref))
    return out


def normalize(doc: dict[str, Any]) -> dict[str, Any]:
    return compact(
        {
            "documentNumber": clean_str(doc.get("document_number")),
            "title": clean_text(doc.get("title")),
            "documentType": clean_str(doc.get("type")),
            "abstract": clean_text(doc.get("abstract")),
            "action": clean_text(doc.get("action")),
            "publicationDate": clean_date(doc.get("publication_date")),
            "effectiveDate": clean_date(doc.get("effective_on")),
            "commentsCloseDate": clean_date(doc.get("comments_close_on")),
            "agencies": _agency_names(doc.get("agencies")),
            "docketIds": [d for d in (doc.get("docket_ids") or []) if d],
            "regulationIdNumbers": [
                r for r in (doc.get("regulation_id_numbers") or []) if r
            ],
            "cfrReferences": _cfr_refs(doc.get("cfr_references")),
            "significant": doc.get("significant"),
            "pageLength": clean_int(doc.get("page_length")),
            "url": clean_str(doc.get("html_url")),
            "pdfUrl": clean_str(doc.get("pdf_url")),
            "source": SOURCE,
        }
    )


def build_params(
    *,
    term: str | None = None,
    document_types: list[str] | None = None,
    agencies: list[str] | None = None,
    published_after: str | None = None,
    published_before: str | None = None,
    order: str = "newest",
    per_page: int = PAGE_SIZE,
) -> dict[str, Any]:
    """The FR API uses PHP-style bracket params; build them explicitly."""
    params: dict[str, Any] = {
        "per_page": per_page,
        "order": order,
        "fields[]": list(FIELDS),
    }
    if term:
        params["conditions[term]"] = term
    if document_types:
        params["conditions[type][]"] = document_types
    if agencies:
        params["conditions[agencies][]"] = agencies
    if published_after:
        params["conditions[publication_date][gte]"] = published_after
    if published_before:
        params["conditions[publication_date][lte]"] = published_before
    return params


async def search(
    client: FedstackClient, *, max_items: int, **filters: Any
) -> AsyncIterator[list[dict[str, Any]]]:
    """Yield pages of normalized documents, following the API's cursor."""
    per_page = min(PAGE_SIZE, max_items)
    params = build_params(per_page=per_page, **filters)

    url: str | None = BASE_URL
    yielded = 0

    while url and yielded < max_items:
        # Only the first request carries params; next_page_url embeds its own.
        payload = await client.request_json(
            "GET", url, params=params if url == BASE_URL else None
        )

        results = payload.get("results") or []
        if not results:
            return

        page = [normalize(d) for d in results][: max_items - yielded]
        yielded += len(page)
        yield page

        url = clean_str(payload.get("next_page_url"))
