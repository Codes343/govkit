#!/usr/bin/env python3
"""Hit every upstream government API for real and assert the data is still sane.

This is the business's early-warning system. Unit tests prove our code is
correct against a *frozen* idea of each API; this proves the APIs themselves
still behave the way we sold them. It runs daily in CI and opens a GitHub issue
on failure, which is the only "monitoring" a zero-headcount business can afford.

Exit code 0 = all sources healthy. 1 = at least one source is broken.
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field

from fedstack.http import FedstackClient
from fedstack.sources import federal_register as fr
from fedstack.sources import grants_gov


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    samples: int = 0
    missing: list[str] = field(default_factory=list)


async def _collect(source_module, *, max_items: int, **filters) -> list[dict]:
    async with FedstackClient(source_module.SOURCE, min_interval=0.05) as client:
        out: list[dict] = []
        async for page in source_module.search(client, max_items=max_items, **filters):
            out.extend(page)
        return out


def _verify(name: str, records: list[dict], required: set[str]) -> Check:
    if not records:
        return Check(name, False, "returned zero records")
    missing = sorted(required - set(records[0]))
    if missing:
        return Check(
            name,
            False,
            f"first record is missing expected fields: {missing}",
            len(records),
            missing,
        )
    return Check(name, True, f"{len(records)} records, schema intact", len(records))


async def check_grants_gov() -> Check:
    records = await _collect(
        grants_gov, max_items=5, keyword="research", statuses=["posted"]
    )
    check = _verify(
        "grants.gov/search2",
        records,
        {"opportunityId", "title", "agencyName", "status", "url"},
    )
    if not check.ok:
        return check

    # The detail endpoint is a separate contract and fails separately.
    async with FedstackClient(grants_gov.SOURCE) as client:
        enriched = await grants_gov.enrich(client, records[:2])
    if any("detailError" in r for r in enriched):
        errors = [r["detailError"] for r in enriched if "detailError" in r]
        return Check("grants.gov/search2", False, f"detail fetch failed: {errors[0]}")
    return Check(
        "grants.gov/search2", True, f"{len(records)} records + detail, schema intact"
    )


async def check_federal_register() -> Check:
    records = await _collect(
        fr, max_items=5, term="energy", document_types=["RULE", "PRORULE"]
    )
    return _verify(
        "federalregister.gov/documents",
        records,
        {"documentNumber", "title", "documentType", "publicationDate", "url"},
    )


CHECKS: list[Callable] = [check_grants_gov, check_federal_register]


async def main() -> int:
    results: list[Check] = []
    for check in CHECKS:
        try:
            results.append(await check())
        except Exception:  # noqa: BLE001 — a crash is itself the finding
            results.append(
                Check(check.__name__, False, traceback.format_exc(limit=3).strip())
            )

    print("## Fedstack upstream smoke test\n")
    for result in results:
        icon = "PASS" if result.ok else "FAIL"
        # ASCII only: this output is read from Windows consoles and CI logs alike.
        print(f"- **{icon}** `{result.name}` - {result.detail}")

    failed = [r for r in results if not r.ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} sources healthy.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
