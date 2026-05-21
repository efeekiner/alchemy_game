from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apothecaria.db.models import Ingredient, Recipe
from apothecaria.domain.models import BrewResult


def combine_ingredients(ingredient_slugs: list[str], session: Session) -> BrewResult:
    """Attempt to match a set of ingredients against every known recipe.

    Use this when the player submits ingredients to the cauldron — either for
    a standalone brew or as part of serving a customer.
    :param ingredient_slugs: Ordered list of ingredient slugs the player combined.
    :param session: Active SQLAlchemy session used to query ingredients and recipes.
    :return: A :class:`BrewResult` describing the matched recipe (or failure).
    """
    if not ingredient_slugs:
        return BrewResult(
            matched_recipe_slug=None,
            matched_recipe_name=None,
            matched_ailment_category=None,
            quality_score=0.0,
            ingredient_slugs=[],
            description="An empty cauldron sits cold.",
        )

    requested = list(ingredient_slugs)
    requested_set = set(requested)

    known = {
        i.slug
        for i in session.scalars(select(Ingredient).where(Ingredient.slug.in_(requested))).all()
    }
    unknown = requested_set - known
    if unknown:
        return BrewResult(
            matched_recipe_slug=None,
            matched_recipe_name=None,
            matched_ailment_category=None,
            quality_score=0.0,
            ingredient_slugs=requested,
            description=f"The cauldron sputters at unknown ingredients: {sorted(unknown)}.",
        )

    for recipe in session.scalars(select(Recipe)).all():
        recipe_slugs = {link.ingredient.slug for link in recipe.ingredient_links}
        if recipe_slugs == requested_set and len(requested) == len(recipe_slugs):
            return BrewResult(
                matched_recipe_slug=recipe.slug,
                matched_recipe_name=recipe.name,
                matched_ailment_category=recipe.ailment_category,
                quality_score=1.0,
                ingredient_slugs=requested,
                description=f"The brew settles into a perfect {recipe.name.lower()}.",
            )

    return BrewResult(
        matched_recipe_slug=None,
        matched_recipe_name=None,
        matched_ailment_category=None,
        quality_score=0.0,
        ingredient_slugs=requested,
        description="The cauldron belches a foul-smelling cloud — an unknown brew.",
    )
