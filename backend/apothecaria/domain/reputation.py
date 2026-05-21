from __future__ import annotations

import json

from sqlalchemy.orm import Session

from apothecaria.db.models import BrewHistory, PlayerState
from apothecaria.domain.models import BrewResult, CustomerInstance, Outcome, ServiceResult


def determine_outcome(brew: BrewResult, customer: CustomerInstance) -> tuple[Outcome, int, str]:
    """Compute the outcome, reputation delta, and customer response for a brew attempt.

    Use this when you need a pure, side-effect-free evaluation of how well a brew
    matched a customer's request (e.g. in tests or dry-run previews).
    :param brew: The result produced by :func:`~apothecaria.domain.brewing.combine_ingredients`.
    :param customer: The customer currently being served.
    :return: A tuple of (outcome enum, reputation delta, flavour-text response).
    """
    if brew.matched_recipe_slug == customer.expected_recipe_slug:
        return (
            Outcome.DELIGHTED,
            10,
            f"{customer.name} beams: 'Yes — exactly what I needed. Thank you.'",
        )
    if brew.matched_recipe_slug is not None:
        if brew.matched_ailment_category == customer.ailment_category:
            return (
                Outcome.NEUTRAL,
                1,
                f"{customer.name} accepts the bottle: "
                "'Not quite what I expected, but I suppose it'll do.'",
            )
        return (
            Outcome.DISAPPOINTED,
            -5,
            f"{customer.name} pushes the bottle back: 'This is not what I asked for.'",
        )
    return (
        Outcome.CONFUSED,
        -2,
        f"{customer.name} sniffs the cloudy mixture, frowns, and shuffles out.",
    )


def apply_outcome(brew: BrewResult, customer: CustomerInstance, session: Session) -> ServiceResult:
    """Compute the outcome and persist reputation change and brew history.

    Use this in the serve-customer flow after brewing: it calls
    :func:`determine_outcome`, updates :class:`~apothecaria.db.models.PlayerState`,
    and appends a :class:`~apothecaria.db.models.BrewHistory` row.
    :param brew: The brew result from combining the player's ingredients.
    :param customer: The customer being served.
    :param session: Active SQLAlchemy session used to read and write game state.
    :return: A :class:`ServiceResult` with outcome, deltas, and customer response text.
    """
    outcome, delta, response = determine_outcome(brew, customer)

    state = session.get(PlayerState, 1)
    if state is None:
        state = PlayerState(id=1, reputation=0, brews_count=0)
        session.add(state)
        session.flush()
    state.reputation += delta
    state.brews_count += 1

    session.add(
        BrewHistory(
            ingredient_slugs=json.dumps(brew.ingredient_slugs),
            matched_recipe_slug=brew.matched_recipe_slug,
            quality_score=brew.quality_score,
            customer_id=customer.id,
            customer_name=customer.name,
            customer_ailment_category=customer.ailment_category,
            expected_recipe_slug=customer.expected_recipe_slug,
            outcome=outcome.value,
            reputation_delta=delta,
        )
    )
    session.flush()

    return ServiceResult(
        outcome=outcome,
        reputation_delta=delta,
        new_reputation=state.reputation,
        customer_response=response,
    )
