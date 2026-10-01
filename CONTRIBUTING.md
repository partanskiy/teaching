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

A `commit-msg` hook in `.githooks/` checks the format, ASCII commit text and subject length. Git LFS hooks upload objects before pushing and maintain files after checkout or merge. Install Git LFS through the system package manager, then initialize and opt in once per clone:

```sh
git lfs install
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
python scripts/build_submission.py --output /tmp/teaching-submission.docx
python scripts/check_plans.py --rebuilt-submission /tmp/teaching-submission.docx
node scripts/check_catalog.js
```

These checks must pass, and generated tracked files must have no uncommitted changes. The temporary submission output avoids unnecessary LFS versions from creation timestamps. When changing rendered plans, prepare the text index, export both documents, and run the full checks:

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

Track official originals, rendered documents and raster images with Git LFS through .gitattributes. Editable vector sources use ordinary Git. Keep download caches, private reference documents and release ZIPs outside Git. Explain substantial additions in the pull request. Run git lfs fsck before pushing and do not bypass the pre-push hook.

## Releasing

See [BINARY_FLOW.md](BINARY_FLOW.md) and the [course release workflow](courses/olympiad-math-10/BINARY_FLOW.md). Ready-to-use files are versioned through Git LFS. Releases provide optional downloadable snapshots; the existing Pages site is built from verified release assets without downloading the full LFS bank.
