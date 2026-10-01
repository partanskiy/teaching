#!/usr/bin/env python3
"""Check English Conventional Commit formatting in a message or Git range."""
import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBJECT = re.compile(
    r'(feat|fix|refactor|docs|test|chore|perf|build|ci|style|revert)'
    r'(\([a-z0-9._/-]+\))?!?: [A-Za-z][\x20-\x7e]*'
)


def check(message):
    lines = message.strip().splitlines()
    if not lines:
        return 'Commit message is empty'
    if not message.isascii():
        return 'Write the entire commit message in English with ASCII punctuation'
    if len(lines[0]) > 72:
        return 'Commit subject exceeds 72 characters'
    if not SUBJECT.fullmatch(lines[0]):
        return 'Expected type(scope): short imperative description'
    return None


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--message-file', type=Path)
    group.add_argument('--range', default='HEAD')
    args = parser.parse_args()
    failures = []
    if args.message_file:
        raw = args.message_file.read_text()
        message = subprocess.run(
            ['git', 'stripspace', '--strip-comments'], input=raw,
            text=True, capture_output=True, check=True, cwd=ROOT
        ).stdout
        error = check(message)
        if error:
            failures.append(error)
        count = 1
    else:
        commits = git('rev-list', args.range).splitlines()
        for commit in commits:
            if len(git('show', '-s', '--format=%P', commit).split()) > 1:
                failures.append(commit[:12] + ': Merge commits are not allowed')
            error = check(git('show', '-s', '--format=%B', commit))
            if error:
                failures.append(commit[:12] + ': ' + error)
        count = len(commits)
    if failures:
        for error in failures:
            print('commit-msg: ' + error)
        raise SystemExit(1)
    print(f'Commit messages passed: {count} checked.')


if __name__ == '__main__':
    main()
