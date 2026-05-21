from __future__ import annotations

import asyncio
import json
import random
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path

from apothecaria.domain.models import CustomerInstance, CustomerTemplate

CUSTOMER_FILE = Path(__file__).resolve().parents[1] / "content" / "customers.json"


def load_templates() -> list[CustomerTemplate]:
    """Load all customer templates from the bundled JSON content file.

    Use this when you need the full pool of templates (e.g. to build a custom
    subset before passing it to :func:`pick_next_template`).
    :return: List of validated :class:`CustomerTemplate` objects.
    """
    rows = json.loads(CUSTOMER_FILE.read_text())
    return [CustomerTemplate.model_validate(r) for r in rows]


def pick_next_template(
    rng: random.Random | None = None,
    templates: list[CustomerTemplate] | None = None,
) -> CustomerTemplate:
    """Pick a random customer template from the pool.

    Use this to decide which customer type arrives next, optionally injecting a
    seeded :class:`random.Random` or a pre-filtered template list for testing.
    :param rng: Optional RNG instance; a fresh :class:`random.Random` is used when omitted.
    :param templates: Optional list of templates to draw from; loads from disk when omitted.
    :return: A randomly selected :class:`CustomerTemplate`.
    """
    rng = rng or random.Random()
    pool = templates if templates is not None else load_templates()
    return rng.choice(pool)


def make_customer(template: CustomerTemplate) -> CustomerInstance:
    """Instantiate a live customer from a template, assigning a fresh UUID and arrival time.

    Use this right after :func:`pick_next_template` to create the customer object
    that will be placed in the :class:`CustomerStore`.
    :param template: The template describing the customer type.
    :return: A new :class:`CustomerInstance` ready to be added to the store.
    """
    return CustomerInstance(
        id=str(uuid.uuid4()),
        template_slug=template.slug,
        name=template.name,
        persona=template.persona,
        ailment_narrative=template.ailment_narrative,
        ailment_category=template.ailment_category,
        expected_recipe_slug=template.expected_recipe_slug,
        sprite=template.sprite,
        arrived_at=datetime.utcnow(),
    )


class CustomerStore:
    """In-memory store of *active* (un-served) customers, keyed by id.

    Customers are ephemeral: after they are served, they leave the store.
    The brew/serve event is recorded persistently in BrewHistory.
    """

    def __init__(self) -> None:
        self._active: dict[str, CustomerInstance] = {}

    def add(self, customer: CustomerInstance) -> None:
        self._active[customer.id] = customer

    def get(self, customer_id: str) -> CustomerInstance | None:
        return self._active.get(customer_id)

    def remove(self, customer_id: str) -> CustomerInstance | None:
        return self._active.pop(customer_id, None)

    def get_oldest(self) -> CustomerInstance | None:
        if not self._active:
            return None
        return min(self._active.values(), key=lambda c: c.arrived_at)

    def size(self) -> int:
        return len(self._active)

    def clear(self) -> None:
        self._active.clear()


async def arrival_loop(
    interval_seconds: float,
    store: CustomerStore,
    on_arrival: Callable[[CustomerInstance], Awaitable[None]],
    rng: random.Random | None = None,
) -> None:
    """Spawn a new customer on a fixed cadence and notify the caller on each arrival.

    Use this when starting the background arrival task during app lifespan;
    cancel the returned asyncio task to stop the loop.
    :param interval_seconds: Seconds to wait between each customer arrival.
    :param store: The in-memory store to which each new customer is added.
    :param on_arrival: Async callback invoked with the new customer after each arrival.
    :param rng: Optional RNG instance; a fresh :class:`random.Random` is used when omitted.
    """
    rng = rng or random.Random()
    while True:
        await asyncio.sleep(interval_seconds)
        template = pick_next_template(rng)
        customer = make_customer(template)
        store.add(customer)
        await on_arrival(customer)
