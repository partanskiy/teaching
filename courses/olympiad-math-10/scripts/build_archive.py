#!/usr/bin/env python3
"""Create a local archive and provenance manifest; extract searchable text."""
import concurrent.futures
import hashlib
import os
import re
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse
from lxml import etree
from collect import ROOT, read_json, write_json


def members(path):
    if path.suffix == '.zip':
        with zipfile.ZipFile(path) as z:
            for member in z.infolist():
                if member.file_size > 35 * 1024 * 1024 or not member.filename.lower().endswith(('.pdf', '.docx')):
                    continue
                yield member.filename, z.read(member)
    elif path.suffix == '.7z':
        listing = subprocess.run(['7z', 'l', '-slt', str(path)], capture_output=True, text=True, check=True).stdout
        for name in re.findall(r'^Path = (.+)$', listing, re.M):
            if not name.lower().endswith(('.pdf', '.docx')):
                continue
            result = subprocess.run(['7z', 'x', '-so', str(path), name], capture_output=True, check=True)
            if len(result.stdout) <= 35 * 1024 * 1024:
                yield name, result.stdout


def extract(item):
    path = ROOT / item['path']
    target = ROOT / 'extracted/full' / (item['id'] + '.txt')
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        if path.suffix == '.pdf':
            result = subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', str(path), str(target)], capture_output=True, text=True)
            if result.returncode:
                item['extraction_error'] = result.stderr.strip()[:500]
                target.write_text('')
        elif path.suffix == '.docx':
            with zipfile.ZipFile(path) as z:
                xml = etree.fromstring(z.read('word/document.xml'))
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            target.write_text('\n'.join(''.join(p.xpath('.//w:t/text()', namespaces=ns)) for p in xml.xpath('//w:p', namespaces=ns)))
    text = target.read_text()
    item['text_path'] = str(target.relative_to(ROOT))
    item['text_characters'] = len(text.strip())
    item['text_pages'] = text.count('\f') if path.suffix == '.pdf' else None
    item['extraction_status'] = 'text' if len(text.strip()) >= 100 else 'requires_visual_reading'
    return item


def main():
    pages = read_json(ROOT / 'data/pages.json', {})
    candidates = read_json(ROOT / 'data/candidates.json', [])
    manifest, failures = [], []
    for candidate in candidates:
        page = pages.get(candidate['url'], {})
        if page.get('status') != 'ok':
            failures.append(dict(candidate, error=page.get('error', 'Not downloaded')))
            continue
        src = ROOT / page['path']
        if src.suffix == '.html':
            if candidate['role'] != 'index':
                failures.append(dict(candidate, error='HTML instead of the requested document'))
            continue
        inputs = list(members(src)) if src.suffix in ['.zip', '.7z'] else [(None, src.read_bytes())]
        for member, content in inputs:
            display_member = member
            if member and not re.search(r'[А-Яа-яЁё]', member) and any(ord(c) > 127 for c in member):
                try:
                    decoded = member.encode('cp437').decode('cp866')
                    if re.search(r'[А-Яа-яЁё]', decoded):
                        display_member = decoded
                except UnicodeError:
                    pass
            suffix = '.pdf' if content.startswith(b'%PDF') else '.docx' if content.startswith(b'PK') else None
            if suffix is None:
                failures.append(dict(candidate, error='Unsupported file signature', member=member))
                continue
            item = dict(candidate)
            if item['stage']=='municipal':
                item['source_index_year']=item['year']
                item['year']=int(item['academic_year'].split('/')[0])
            if item['stage'] == 'municipal' and item['region_slug'] in ['msk', 'moscow']:
                item['region_slug'], item['region'] = 'moscow', 'Москва'
            if re.search(r'/(?:usl|resh)[_-]?0?10[_.]', candidate['url'], re.I):
                item['grade_scope'] = [10]
            grade_range=re.search(r'/([5-9])[-_]11\.pdf$',candidate['url'],re.I)
            if grade_range:
                item['grade_scope']=list(range(int(grade_range[1]),12))
            role = item['role']
            if role == 'bundle':
                role = 'combined'
            if 'iii-day' in candidate['url'] or re.search(r'/[12]\.pdf$', candidate['url']):
                role = 'tasks'
            if member:
                m = display_member.lower()
                role = 'combined' if 'решени' in m and 'критери' in m else 'solutions' if 'решени' in m else 'criteria' if 'критери' in m else 'tasks'
                if candidate['role'] in ['requirements_bundle', 'methodology_bundle']:
                    role = candidate['role'].replace('_bundle', '')
            elif role.endswith('_bundle'):
                role = role.replace('_bundle', '')
            item['role'] = role
            item['bundle_member'] = display_member
            if display_member != member:
                item['bundle_member_original'] = member
            item['id'] = hashlib.sha256((candidate['url'] + (member or '')).encode()).hexdigest()[:14]
            item['sha256'] = hashlib.sha256(content).hexdigest()
            item['bytes'] = len(content)
            item['download_url'] = page.get('download_url', page.get('final_url'))
            item['retrieved_at'] = page['retrieved_at']
            if 'provenance' not in item:
                item['provenance'] = 'federal_publisher' if 'edsoo.ru' in candidate['url'] else 'organizer'
            original_name = Path(display_member).name if member else unquote(Path(urlparse(candidate['url']).path).name)
            if not original_name.lower().endswith(suffix):
                original_name = role + suffix
            filename = re.sub(r'[^\w.()-]+', '_', original_name, flags=re.U)
            dest = ROOT / 'archive' / item['competition'] / item['stage'] / item['academic_year'].replace('/', '-') / item['region_slug'] / (item['id'] + '_' + filename)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                if member is None:
                    os.link(src, dest)
                else:
                    dest.write_bytes(content)
            item['path'] = str(dest.relative_to(ROOT))
            manifest.append(item)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        manifest = list(pool.map(extract, manifest))
    write_json(ROOT / 'data/documents.json', manifest)
    write_json(ROOT / 'data/download-failures.json', failures)
    print('Documents:', len(manifest), 'Failed candidates:', len(failures))


if __name__ == '__main__':
    main()
