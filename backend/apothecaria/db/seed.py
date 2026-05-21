from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, select
from sqlalchemy.orm import Session

from apothecaria.db.models import (
    Ingredient,
    PlayerState,
    Recipe,
    RecipeIngredient,
)
from apothecaria.domain.models import IngredientSeed, RecipeSeed

CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"


def _load_json(name: str) -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = json.loads((CONTENT_DIR / name).read_text())
    return data


def seed_database(connection: Connection) -> None:
    """Idempotently load content JSON into the DB using upsert semantics.

    Use this when initialising or refreshing the database from the content
    JSON files (e.g. after a student edits ingredients or recipes in Module 1).
    Existing rows matched by slug are updated; new rows are inserted.
    :param connection: An open SQLAlchemy :class:`~sqlalchemy.engine.Connection`
        (typically obtained from ``engine.connect()``).
    """
    with Session(bind=connection) as session:
        _seed_ingredients(session)
        _seed_recipes(session)
        _seed_player_state(session)
        session.commit()


def _seed_ingredients(session: Session) -> None:
    rows = [IngredientSeed.model_validate(r) for r in _load_json("ingredients.json")]
    existing = {i.slug: i for i in session.scalars(select(Ingredient)).all()}
    for row in rows:
        if row.slug in existing:
            ing = existing[row.slug]
            ing.name = row.name
            ing.lore = row.lore
            ing.sprite = row.sprite
        else:
            session.add(Ingredient(**row.model_dump()))
    session.flush()


def _seed_recipes(session: Session) -> None:
    rows = [RecipeSeed.model_validate(r) for r in _load_json("recipes.json")]
    by_slug = {i.slug: i for i in session.scalars(select(Ingredient)).all()}
    existing = {r.slug: r for r in session.scalars(select(Recipe)).all()}
    for row in rows:
        if row.slug in existing:
            recipe = existing[row.slug]
            recipe.name = row.name
            recipe.ailment_category = row.ailment_category
            recipe.lore = row.lore
            recipe.sprite = row.sprite
            recipe.ingredient_links.clear()
            session.flush()
            recipe.ingredient_links = [
                RecipeIngredient(ingredient_id=by_slug[s].id) for s in row.ingredients
            ]
        else:
            recipe = Recipe(
                slug=row.slug,
                name=row.name,
                ailment_category=row.ailment_category,
                lore=row.lore,
                sprite=row.sprite,
            )
            recipe.ingredient_links = [
                RecipeIngredient(ingredient_id=by_slug[s].id) for s in row.ingredients
            ]
            session.add(recipe)
    session.flush()


def _seed_player_state(session: Session) -> None:
    if session.get(PlayerState, 1) is None:
        session.add(PlayerState(id=1, reputation=0, brews_count=0))
        session.flush()


def main() -> None:
    """Initialise the database schema and seed it from the content JSON files.

    Use this as the CLI entry point via ``python -m apothecaria.db.seed``
    or ``make seed`` to (re-)populate a local database.
    """
    from apothecaria.db.session import engine, init_db

    init_db()
    with engine.connect() as conn:
        seed_database(conn)
    print("Database seeded.")


if __name__ == "__main__":
    main()
