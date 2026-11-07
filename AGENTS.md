# Repository instructions

- Before continuing a course, read its AGENTS.md and HANDOFF.md. For olympiad-math-10, start with courses/olympiad-math-10/HANDOFF.md for current progress, materials, unknowns, build commands, and uncommitted local work.
- Write all commit messages in English using Conventional Commits. Keep each commit focused on one logical change.
- Follow CONTRIBUTING.md. After the initial import, use pull requests and rebase merges. Never force-push main.
- Keep courses in separate directories under courses/. Run commands from the corresponding course directory.
- Update submission programmes and working plans through shared source data; verify their synchronization after rebuilding.
- Track official originals, rendered plans and raster images through Git LFS. Keep download caches and release ZIPs outside Git. Editable vector sources use ordinary Git. Follow BINARY_FLOW.md.
- Use plain punctuation and ASCII formatting while preserving Russian letters, including ё, and required mathematical symbols.
- Use system Python and package-manager dependencies. Do not install dependencies through pip or pipx on the user's laptop.
