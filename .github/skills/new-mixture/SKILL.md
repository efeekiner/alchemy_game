---
name: new-mixture
description: Use when the user asks to add a new mixture, recipe, potion, or brew to the Apothecaria game. Adds a recipe to the JSON seed so it shows up in /api/recipes and is brewable via /api/brew.
---

# New Mixture

Adding a new mixture means adding a recipe entry so the apothecary recognizes it: it shows up in `/api/recipes` and can be brewed via `/api/brew` after re-seeding.

## Required inputs

Before making any changes, confirm the user has provided:

- **slug** — lowercase, `snake_case`, unique among existing recipes. e.g. `fog_veil`.
- **name** — human display name. e.g. "Fog Veil".
- **ailment_category** — short tag (`confusion`, `wound`, `sleep`, `fatigue`, `anxiety`, `sorrow`, …). Reuse an existing category when possible.
- **ingredients** — list of slugs that **must already exist** in `backend/apothecaria/content/ingredients.json`.
- **lore** — one-line flavor description, matching the sensory, evocative tone of existing entries.

If anything is missing or ambiguous, ask the user before proceeding.

## Preconditions

- The working tree must be clean (`git status` shows no changes). If it isn't, stop and ask the user to commit or stash first.
- `gh` (GitHub CLI) must be installed and authenticated for the PR step. If `gh auth status` fails, stop after the test step and tell the user to run `gh auth login` before continuing.

## Steps

1. **Validate.** Read `backend/apothecaria/content/ingredients.json` and confirm every requested ingredient slug exists. If any are missing, stop and tell the user to add the ingredient first — that's a separate task, not part of this skill.

2. **Confirm uniqueness.** Read `backend/apothecaria/content/recipes.json` and confirm the new `slug` and the new ingredient-set are both unique. The brewing engine matches recipes by ingredient set, so two recipes with identical ingredient sets would collide.

3. **Add the entry to `backend/apothecaria/content/recipes.json`.** Match the existing entries' shape and one-line-per-object formatting exactly. Trailing newline preserved.

4. **Re-seed:**
   ```bash
   make seed
   ```

5. **Extend tests.** Add an assertion in `backend/tests/test_api_recipes.py` that the new mixture is present in the API response with its expected ingredients. Follow the patterns already in that file.

6. **Run the test suite:**
   ```bash
   make test
   ```

7. **Branch, commit, push, open the PR.** Create a branch named `add-mixture-<slug>`, commit just the two changed files with a Conventional Commit message, push, and open a PR with the body template below.

   ```bash
   git checkout -b add-mixture-<slug>
   git add backend/apothecaria/content/recipes.json backend/tests/test_api_recipes.py
   git commit -m "feat(content): add <name> mixture"
   git push -u origin add-mixture-<slug>
   gh pr create --title "Add <name> mixture" --body "$(cat <<'EOF'
   ## Summary
   Adds a new mixture **<name>** (`<slug>`) for the `<ailment_category>` ailment.

   ## Recipe
   - **Ingredients:** <comma-separated ingredient slugs>
   - **Lore:** <lore line>

   ## Verification
   - `make seed` upserts the new recipe.
   - `make test` passes; extended `test_api_recipes.py` with an assertion that this mixture appears in the API response with its expected ingredients.

   ## What this PR does *not* touch
   API routes, brewing logic, DB models, frontend. The seed loader and DB-backed brew-matching pick up the new recipe automatically.
   EOF
   )"
   ```

   Substitute `<slug>`, `<name>`, `<ailment_category>`, the ingredient list, and the lore line into both the title and body. Print the PR URL `gh` returns.

8. **Show the diff** with `/diff` and summarize the change.

## Files this skill touches

- `backend/apothecaria/content/recipes.json` (always)
- `backend/tests/test_api_recipes.py` (always)
- One new git branch + one PR (always)
- *Not* the API routes, brewing logic, or frontend — those auto-discover recipes from the DB.

## What NOT to do

- Don't add new ingredients here. If the recipe needs one, stop and tell the user.
- Don't edit the API, brewing logic, or DB models.
- Don't add a database migration — the JSON seed is the source of truth; `make seed` upserts.
- Don't touch the frontend.
