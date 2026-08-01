"""Billing is the revenue path — it gets the most careful tests in the repo."""

from __future__ import annotations

from typing import Any

import pytest

from govkit.billing import EVENT_ACTOR_START, EVENT_DATASET_ITEM, Billing


class ChargeResult:
    def __init__(self, limit_reached: bool = False) -> None:
        self.event_charge_limit_reached = limit_reached


class FakeActor:
    """Stands in for apify.Actor, recording what would have been billed."""

    def __init__(self, *, limit_after: int | None = None, charge_raises: bool = False):
        self.pushed: list[dict[str, Any]] = []
        self.push_events: list[str | None] = []
        self.charges: list[tuple[str, int]] = []
        self._limit_after = limit_after
        self._charge_raises = charge_raises

    async def push_data(self, data, event_name=None):
        self.pushed.append(data)
        self.push_events.append(event_name)
        reached = self._limit_after is not None and len(self.pushed) >= self._limit_after
        return ChargeResult(reached)

    async def charge(self, event_name: str, count: int = 1):
        if self._charge_raises:
            raise RuntimeError("billing backend unavailable")
        self.charges.append((event_name, count))
        return ChargeResult(False)


async def test_charges_start_once_only():
    actor = FakeActor()
    billing = Billing(actor, enabled=True)
    await billing.charge_start()
    await billing.charge_start()
    assert actor.charges == [(EVENT_ACTOR_START, 1)]


async def test_each_pushed_item_is_billed_as_a_dataset_item():
    actor = FakeActor()
    billing = Billing(actor, enabled=True)
    accepted = await billing.push_many([{"i": 1}, {"i": 2}, {"i": 3}])
    assert accepted == 3
    assert actor.push_events == [EVENT_DATASET_ITEM] * 3
    assert billing.items_charged == 3


async def test_stops_immediately_when_the_users_spend_ceiling_is_hit():
    actor = FakeActor(limit_after=2)
    billing = Billing(actor, enabled=True)
    accepted = await billing.push_many([{"i": n} for n in range(10)])

    # The item that tripped the limit was still delivered, so it is still billed;
    # everything after it must not be pushed at all.
    assert accepted == 2
    assert len(actor.pushed) == 2
    assert billing.limit_reached is True

    # Any later push is refused without touching the dataset.
    assert await billing.push({"i": 99}) is False
    assert len(actor.pushed) == 2


async def test_disabled_billing_still_delivers_data_but_charges_nothing():
    """Local runs and CI smoke tests must exercise the same code path."""
    actor = FakeActor()
    billing = Billing(actor, enabled=False)
    await billing.charge_start()
    assert await billing.push({"i": 1}) is True

    assert actor.charges == []
    assert actor.push_events == [None]
    assert actor.pushed == [{"i": 1}]


async def test_a_failing_charge_never_kills_the_run():
    """Losing a nickel beats losing a customer."""
    actor = FakeActor(charge_raises=True)
    billing = Billing(actor, enabled=True)
    await billing.charge_start()  # must not raise
    assert await billing.push({"i": 1}) is True


@pytest.mark.parametrize("env_value,expected", [("5.0", True), (None, False)])
async def test_billing_auto_enables_from_the_platform_env_var(
    monkeypatch, env_value, expected
):
    if env_value is None:
        monkeypatch.delenv("ACTOR_MAX_TOTAL_CHARGE_USD", raising=False)
    else:
        monkeypatch.setenv("ACTOR_MAX_TOTAL_CHARGE_USD", env_value)

    actor = FakeActor()
    billing = Billing(actor)
    await billing.push({"i": 1})
    assert (actor.push_events == [EVENT_DATASET_ITEM]) is expected
