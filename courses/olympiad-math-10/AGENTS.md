# Project instructions

- Read HANDOFF.md before continuing this course. Use session outcomes for actual progress, data/calendar.json for dated calendar evidence, and data/operational-plan.json for proposed dates. Never infer that a prepared or issued task was solved.
- Before preparing the next lesson, account for course/sessions/2026-10-31/plan.json. The teacher has not yet reported solved numbers from that session. A new clone or worktree does not include this working directory's uncommitted materials.
- Write all commit messages in English using Conventional Commits: type(scope): short imperative description.
- Keep commits small and focused on one logical change. Generated datasets and reports may be large, but must be committed separately from unrelated implementation changes.
- Update both the submission programme and working plan through their shared data. Run scripts/check_plans.py after building documents.
- Track official PDFs, rendered DOCX/PDF and raster images through Git LFS. Keep download caches, private reference documents and Release ZIPs outside Git. Follow BINARY_FLOW.md.
- Use plain punctuation and ASCII formatting. Keep Russian letters, including ё, and mathematical symbols required by source material. Avoid decorative Unicode punctuation.
- Use the installed system Python and libraries; do not install dependencies through pip or pipx on the user's laptop.
- Prepare new student handouts in Typst using course/templates/handout.typ. Use student.typ as the editable print source and session.json for session metadata and programme links.
- Print two identical A5 handouts side by side on one landscape A4 sheet. Each A5 half has one task column, centered course and worksheet titles, and the date at the top right. Give every task its own heading "Задача N (source)", with the source in italics and without the word "Источник". Put the statement below the heading and leave space between tasks. Keep the ten-task format unless the teacher requests a different count.
- For formulas that need a line break at an operation or relation sign, insert an explicit break and repeat that sign at the start of the next line. Recheck these fixed breaks after changing the font, text, or available width.
- Add a thin dashed vertical cutting guide at the center of the landscape A4 sheet, between the two A5 handouts.
- Calibrate regional preparation by solution depth, not only by the official stage or task number. The teacher assessed tasks 1-6 of the basic 2026-10-17 handout as near-oral warmups. Use substantive multi-step proofs for the main regional training and keep warmups separate from advanced selections.
- The teacher reports that the group can work through most of a ten-task handout in one 90-minute session, including independent solutions. Plan for this pace with a short entry task and a substantive main selection; do not automatically cap a session at two or three tasks. Record actual completed tasks after class rather than assuming the whole handout was solved.
- Calibrate pace by the topic and latest reported outcomes. On 2026-10-24 the class solved only geometry tasks 1-4; tasks 5-10 remain available. The 2026-10-17 advanced handout had only been touched briefly as of 2026-10-31. Do not carry the introductory number-theory pace over to proof-heavy geometry without checking actual progress.
