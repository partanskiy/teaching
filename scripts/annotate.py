#!/usr/bin/env python3
"""Merge reviewed classifications from research/annotations*.txt."""
from collect import ROOT, read_json, write_json

annotations = read_json(ROOT / 'data/annotations.json', {})
for path in sorted((ROOT / 'research').glob('annotations*.txt')):
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        task_id, topics, methods, summary, difficulty, *extra = line.split('|')
        annotations[task_id] = dict(topics=topics.split(','), methods=methods.split(',') if methods else [],
                                   summary=summary, difficulty=int(difficulty), review_status='statement_reviewed')
        if extra and extra[0]:
            annotations[task_id]['solution_key'] = extra[0]
            annotations[task_id]['review_status'] = 'solution_reviewed'
write_json(ROOT / 'data/annotations.json', annotations)
print('Reviewed annotations:', len(annotations))
