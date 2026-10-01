# Contributing to teaching

This follows the contribution policy used in [synchrogit](https://github.com/partanskiy/synchrogit/blob/main/CONTRIBUTING.md), adapted to teaching materials.

## Branch policy

- `main` is protected. After the initial repository import, all changes go through pull requests.
- Merge mode: **rebase only**. Squash and merge-commit modes are disabled so history stays linear and individual commits are preserved.
- Force-pushing to `main` and deleting `main` are not allowed.

## Commit messages

Write every commit message in English using **Conventional Commits**:

```text
<type>[(scope)][!]: <short imperative description>
```

Allowed types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `build`, `ci`, `style`, `revert`.

Keep the subject within 72 characters. Keep each commit small and focused on one logical change. Commit large generated datasets separately from unrelated code or documentation changes. Write commit bodies in English as well.

Examples:

```text
feat(catalog): add regional geometry tasks
fix(plans): align lesson hours across both programmes
docs(course): explain the invariant method
```

Releases are tag-driven and do not require special release commits. Before merging, rewrite temporary fixup or squash commits into the required format. Merge commits are not accepted.

## Local hooks

A `commit-msg` hook in `.githooks/` checks the format, ASCII commit text and subject length. Opt in once per clone:

```sh
git config core.hooksPath .githooks
```

CI runs the same checker on every commit of a pull request. The hook is a convenience; English wording and sensible commit scope still require human review.

## Development loop

From the repository root:

```sh
python tools/check_commit_messages.py
cd courses/olympiad-math-10
python scripts/make_course.py
python scripts/publish.py
python scripts/build_submission.py
python scripts/check_plans.py --submission-only
node scripts/check_catalog.js
```

These source checks must pass, and generated tracked files must have no uncommitted changes. When changing rendered plans, also restore the official archive, export both documents, and run the full checks:

```sh
python scripts/restore_materials.py
python scripts/export_documents.py
python scripts/check_plans.py
python scripts/validate.py
```

Use system packages for Python dependencies. Do not install them through pip or pipx on the maintainer's laptop.

## Course and source changes

Keep each course under `courses/`. Update the submission programme and working plan through their shared source data. The submission document must retain its administrative format and must not contain repository links or internal task IDs.

Record the original publisher, URL, class, stage, season and checksum for every source document. Distinguish manually reviewed task labels from provisional automatic labels. New downloads and changed originals must pass archive integrity checks before publication.

Keep large originals, rendered documents and download caches outside Git. Small optimized illustrations and editable vector sources may be tracked; explain substantial additions in the pull request.

## Releasing

See [BINARY_FLOW.md](BINARY_FLOW.md) and the [course release workflow](courses/olympiad-math-10/BINARY_FLOW.md). Ready-to-use files live in Releases; the Pages site is built from the source catalogue and verified release assets.
