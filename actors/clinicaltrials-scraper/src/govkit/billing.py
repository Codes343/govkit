"""Pay-per-event billing wrapper.

Two rules govern this module, and they are the whole business:

1. Never charge for something we did not deliver. Charging happens *after* an
   item is written to the dataset, never in advance and never in a batch at the
   end of a run (a run can be aborted, and Apify's guidance is to bill work as
   it completes).
2. Never charge past the user's ceiling. Apify exposes it as
   ``ACTOR_MAX_TOTAL_CHARGE_USD``; the SDK reports it per-charge via
   ``event_charge_limit_reached``. When we hit it we stop cleanly and tell the
   user why, rather than silently truncating.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

EVENT_ACTOR_START = "actor-start"
EVENT_DATASET_ITEM = "dataset-item"


class Billing:
    """Charges pay-per-event usage and enforces the user's spend ceiling.

    Degrades to a no-op when running outside a monetized platform run (local
    development, CI smoke tests), so the same code path is exercised everywhere.
    """

    def __init__(self, actor: Any, *, enabled: bool | None = None) -> None:
        self._actor = actor
        self._limit_reached = False
        self._items_charged = 0
        self._start_charged = False
        if enabled is None:
            enabled = bool(os.environ.get("ACTOR_MAX_TOTAL_CHARGE_USD"))
        self._enabled = enabled

    @property
    def limit_reached(self) -> bool:
        return self._limit_reached

    @property
    def items_charged(self) -> int:
        return self._items_charged

    async def charge_start(self) -> None:
        """Bill the one-off run fee. Safe to call more than once."""
        if self._start_charged or not self._enabled:
            self._start_charged = True
            return
        self._start_charged = True
        await self._charge(EVENT_ACTOR_START, 1)

    async def push(self, item: dict[str, Any]) -> bool:
        """Write one record to the dataset and bill for it.

        Returns True if the record was *delivered*. Note that the record which
        trips the spend ceiling is still delivered and still billed, so it
        returns True while ``limit_reached`` flips to True — callers stop on
        ``limit_reached``, not on the return value. Conflating the two
        previously caused the run summary to under-report delivered rows by one.
        """
        if self._limit_reached:
            return False

        if not self._enabled:
            await self._actor.push_data(item)
            self._items_charged += 1
            return True

        result = await self._actor.push_data(item, EVENT_DATASET_ITEM)
        self._items_charged += 1

        if getattr(result, "event_charge_limit_reached", False):
            self._limit_reached = True
            logger.warning(
                "Charge limit reached after %d items; stopping cleanly.",
                self._items_charged,
            )
        return True

    async def push_many(self, items: list[dict[str, Any]]) -> int:
        """Push a page of records. Returns how many were actually delivered."""
        accepted = 0
        for item in items:
            if not await self.push(item):
                break
            accepted += 1
            if self._limit_reached:
                break
        return accepted

    async def _charge(self, event_name: str, count: int) -> None:
        try:
            result = await self._actor.charge(event_name=event_name, count=count)
        except Exception as exc:  # noqa: BLE001 — billing must never kill a run
            # A failed charge costs us money but a crash costs us a customer.
            logger.error("Charge for %r failed: %s", event_name, exc)
            return
        if getattr(result, "event_charge_limit_reached", False):
            self._limit_reached = True
