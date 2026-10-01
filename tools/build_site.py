#!/usr/bin/env python3
"""Build the public catalogue with verified PDFs outside Git history."""
import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '_site'
TEXT_SUFFIXES = {'.html', '.js', '.css', '.json', '.csv', '.md', '.txt', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.avif', '.gif'}
READING_CSS = '''body{max-width:960px;margin:32px auto;padding:0 20px;font:17px/1.65 system-ui,sans-serif;color:#172c36;background:#fbfaf6}a{color:#075d76}h1,h2,h3{line-height:1.25}table{border-collapse:collapse;width:100%;display:block;overflow-x:auto}th,td{padding:8px;border:1px solid #bbc8cd;text-align:left}pre{overflow:auto;padding:16px;background:#edf1f2}code{font-size:.9em}img{max-width:100%}.course{padding:20px;margin:24px 0;border:1px solid #bbc8cd;border-radius:8px}'''


def load(path):
    return json.loads(path.read_text())


def checksum(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def safe_path(base, value):
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe asset path: ' + value)
    destination = base / path
    if not destination.resolve().is_relative_to(base.resolve()):
        raise ValueError('Asset path outside course: ' + value)
    return destination


def restore_plans(module, release, local):
    for asset in release['plans'].values():
        path = safe_path(module, asset['path'])
        if not path.is_file() or checksum(path) != asset['sha256']:
            if local:
                raise ValueError('Local plan differs from release manifest: ' + str(path))
            request = Request(asset['url'], headers={'User-Agent': 'teaching-pages'})
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                try:
                    with urlopen(request, timeout=60) as response:
                        shutil.copyfileobj(response, stream)
                    stream.flush()
                    if checksum(temporary) != asset['sha256'] or temporary.stat().st_size != asset['bytes']:
                        raise ValueError('Downloaded plan checksum or size differs')
                    temporary.replace(path)
                finally:
                    temporary.unlink(missing_ok=True)
        if path.stat().st_size != asset['bytes']:
            raise ValueError('Plan size differs: ' + str(path))


def rewrite_markdown_links(text):
    def replace(match):
        prefix, value, suffix = match.groups()
        url = urlsplit(value)
        if not url.scheme and not url.netloc and url.path.endswith('.md'):
            value = urlunsplit(('', '', url.path[:-3] + '.html', url.query, url.fragment))
        return prefix + value + suffix
    return re.sub(r'(<a\b[^>]*\bhref=["\'])([^"\']+)(["\'])', replace, text)


def render_markdown(output):
    for source in sorted(output.rglob('*.md')):
        target = source.with_suffix('.html')
        css = os.path.relpath(output / 'reading.css', target.parent)
        subprocess.run([
            'pandoc', str(source), '--from=gfm', '--to=html5', '--standalone',
            '--metadata=lang:ru', '--metadata=title:' + source.stem,
            '--css=' + css, '--output=' + str(target)
        ], check=True)
        target.write_text(rewrite_markdown_links(target.read_text()))
    for path in output.rglob('index.html'):
        path.write_text(rewrite_markdown_links(path.read_text()))


def check_links(output):
    count = 0
    for path in output.rglob('*.html'):
        for value in re.findall(r'(?:href|src)=["\']([^"\']+)["\']', path.read_text()):
            url = urlsplit(html.unescape(value))
            if url.scheme or url.netloc or not url.path:
                continue
            target = (path.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(output.resolve()) or not target.exists():
                raise ValueError(f'Broken site link in {path.relative_to(output)}: {value}')
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-assets', action='store_true', help='Use locally verified originals and plans without network access')
    args = parser.parse_args()
    cache = ROOT / '_build'
    cache.mkdir(exist_ok=True)
    modules = sorted(p.parent.parent for p in (ROOT / 'courses').glob('*/data/release.json'))
    if not modules:
        raise ValueError('No published courses found')
    courses = []
    with tempfile.TemporaryDirectory(prefix='site-', dir=cache) as temporary:
        output = Path(temporary)
        for module in modules:
            release = load(module / 'data/release.json')
            if not args.local_assets:
                subprocess.run([sys.executable, str(module / 'scripts/restore_materials.py')], check=True, cwd=module)
            documents = load(module / 'data/documents.json')
            for document in documents:
                path = safe_path(module, document['path'])
                if checksum(path) != document['sha256'] or path.stat().st_size != document['bytes']:
                    raise ValueError('Official document differs: ' + document['path'])
            restore_plans(module, release, args.local_assets)
            subprocess.run([sys.executable, str(module / 'scripts/check_plans.py')], check=True, cwd=module)
            subprocess.run(['node', str(module / 'scripts/check_catalog.js')], check=True, cwd=module)
            destination = output / module.relative_to(ROOT)
            for directory in ['site', 'course', 'research', 'data', 'scripts', 'media']:
                for path in (module / directory).rglob('*'):
                    if path.is_file() and path.suffix in TEXT_SUFFIXES | {'.py', '.pdf', '.docx'} and '__pycache__' not in path.parts:
                        target = destination / path.relative_to(module)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(path, target)
            for document in documents:
                path = module / document['path']
                target = destination / document['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
            for name in ['index.html', 'README.md', 'BINARY_FLOW.md', 'NOTICE.md']:
                shutil.copyfile(module / name, destination / name)
            program = load(module / 'data/program.json')
            stats = load(module / 'data/statistics.json')
            courses.append({'path': str(module.relative_to(ROOT)), 'title': program['title'] + ', ' + str(program['grade']) + ' класс', 'year': program['academic_year'], 'documents': len(documents), 'tasks': stats['task_cards'], 'release': release['tag']})
        (output / 'reading.css').write_text(READING_CSS + '\n')
        for name in ['README.md', 'CONTRIBUTING.md', 'BINARY_FLOW.md']:
            shutil.copyfile(ROOT / name, output / name)
        cards = ''.join(
            '<section class="course"><h2>' + html.escape(course['title']) + '</h2><p>' + html.escape(course['year']) + ': ' + str(course['documents']) + ' документов, ' + str(course['tasks']) + ' карточек задач.</p><p><a href="' + course['path'] + '/index.html">Открыть каталог и план занятий</a> / <a href="' + course['path'] + '/README.html">Описание курса и готовые документы</a></p></section>' for course in courses
        )
        (output / 'index.html').write_text('<!doctype html>\n<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Teaching - учебные материалы</title><link rel="stylesheet" href="reading.css"></head><body><h1>Teaching</h1><p>Учебные материалы Партанского Ильи Михайловича: банки задач, программы и рабочие планы.</p>' + cards + '<p><a href="https://github.com/partanskiy/teaching">Репозиторий</a> / <a href="https://github.com/partanskiy/teaching/releases">Скачать готовые комплекты</a> / <a href="BINARY_FLOW.html">Хранение и обновление файлов</a></p></body></html>\n')
        (output / '.nojekyll').write_text('')
        render_markdown(output)
        links = check_links(output)
        total = sum(path.stat().st_size for path in output.rglob('*') if path.is_file())
        if total >= 900_000_000:
            raise ValueError('Site exceeds the project budget of 900 MB; move bulky material to download-only assets before publishing')
        report = {'courses': courses, 'bytes': total, 'links_checked': links}
        (output / 'site-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        if OUTPUT.exists():
            shutil.rmtree(OUTPUT)
        shutil.copytree(output, OUTPUT)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
