#!/usr/bin/env python3
"""Discover links with their source, year, stage, region and document role."""
import re
from collect import ROOT, links, read_json, write_json

pages = read_json(ROOT / 'data/pages.json', {})
candidates = read_json(ROOT / 'data/candidates.json', [])
seen = {x['url'] for x in candidates}
urls = []


def add(link, **meta):
    if link['url'] not in seen:
        candidates.append(dict(meta, url=link['url'], label=link['text']))
        seen.add(link['url'])
    urls.append(link['url'])


for parent in list(candidates):
    if parent['role'] != 'index' or pages.get(parent['url'], {}).get('status') != 'ok':
        continue
    for link in links(pages[parent['url']]):
        u, text = link['url'], link['text']
        if not u.lower().endswith('.pdf'):
            continue
        if parent['stage'] == 'regional' and ('iii' in u or '10' in u or 'услов' in text or 'решен' in text):
            role = 'tasks' if 'day' in u or 'услов' in text.lower() else 'combined'
        elif parent['stage'] == 'municipal' and (
            re.search(r'\b10\s*(?:класс|кл)', text, re.I)
            or re.search(r'/(?:usl|resh)[_-]?0?10(?:[_.-])', u, re.I)
            or 'usl_7-11' in u or u.endswith('/7-11.pdf')
        ):
            role = 'tasks' if 'usl' in u or u.endswith('/7-11.pdf') else 'combined'
        else:
            continue
        meta = {k: v for k, v in parent.items() if k not in ['url', 'label', 'role', 'source_page']}
        if 'usl_7-11' in u or u.endswith('/7-11.pdf'):
            meta['grade_scope'] = [7, 8, 9, 10, 11]
        add(link, **meta, role=role, source_page=parent['url'])

for source, item in pages.items():
    if 'mmo.mccme.ru/' not in source or item['status'] != 'ok' or '/okrug/' in source:
        continue
    match = re.search(r'/((?:19|20)\d\d)/', source)
    if not match or not 2010 <= int(match[1]) <= 2026:
        continue
    year = int(match[1])
    for link in links(item):
        target, text = link['url'], link['text'].lower()
        if not target.lower().endswith('.pdf'):
            continue
        if re.search(r'(?:[-_/])(?:var)?0?10(?:[-_.])', target):
            role = 'criteria' if 'krit' in target else 'solutions' if 'sol' in target else 'combined'
            if 'var10' in target:
                role = 'tasks'
            scope = [10]
        elif re.search(r'/(?:\d+mmo|var(?:-20\d\d)?)\.pdf$', target):
            role = 'combined' if re.search(r'\d+mmo', target) else 'tasks'
            scope = [8, 9, 10, 11]
        else:
            continue
        add(link, source_page=source, competition='mosh', stage='main', year=year,
            academic_year=f'{year-1}/{year}', region='Москва', region_slug='moscow',
            role=role, grade_scope=scope)

source = 'https://zsfond.ru/vsosh/regionalnyj-etap/matematika-regionalnyj-etap/'
if pages.get(source, {}).get('status') == 'ok':
    for link in links(pages[source]):
        u, text = link['url'], link['text'].lower()
        if not u.endswith('.pdf') or not ('10' in text or '9-11' in text):
            continue
        if any(w in text for w in ['протокол', 'приказ']):
            continue
        match = re.search(r'/uploads/(20\d\d)/', u)
        if not match:
            continue
        year = int(match[1])
        role = 'criteria' if 'критер' in text else 'solutions' if 'решени' in text else 'tasks'
        add(link, source_page=source, competition='vsosh', stage='regional', year=year,
            academic_year=f'{year-1}/{year}', region='Свердловская область', region_slug='sverdlovsk',
            role=role, grade_scope=[9, 10, 11] if '9-11' in text else [10])

for source in ['https://vserosolimp.edsoo.ru/region_way', 'https://vserosolimp.edsoo.ru/school_way']:
    if pages.get(source, {}).get('status') != 'ok':
        continue
    ll = links(pages[source])
    if 'region_way' in source:
        maths = [x for x in ll if x['text'] == 'Математика']
        for year, link in zip(range(2022, 2027), maths):
            add(link, source_page=source, competition='vsosh', stage='regional', year=year,
                academic_year=f'{year-1}/{year}', region='Федеральный комплект', region_slug='federal',
                role='bundle', grade_scope=[9, 10, 11])
        for link in ll:
            if '2025/26' in link['text'] and 'Требования' in link['text']:
                add(link, source_page=source, competition='vsosh', stage='regional', year=2026,
                    academic_year='2025/2026', region='Федеральные требования', region_slug='federal',
                    role='requirements_bundle', grade_scope=[9, 10, 11])
    else:
        for link in ll:
            if link['text'] == 'Математика МР ШиМЭ 2026/27':
                add(link, source_page=source, competition='vsosh', stage='municipal', year=2027,
                    academic_year='2026/2027', region='Федеральные рекомендации', region_slug='federal',
                    role='methodology_bundle', grade_scope=[10])

urls += [
    'https://olimpiada.ru/activity/72/tasks/2025',
    'https://olimpiada.ru/activity/72/tasks/2024',
    'https://olimpiada.ru/activity/72/tasks/2023',
    'https://mos.olimpiada.ru/subjects/matematika',
    'https://mmo.mccme.ru/2026/',
    'https://mmo.mccme.ru/2011/mmo2011.htm',
    'https://olympiads.mccme.ru/vmo/2016/index.htm#pdf',
    'https://olympiads.mccme.ru/vmo/2017/index.htm#pdf',
    'https://olympiads.mccme.ru/vmo/2014/index.htm#pdf',
    'https://olympiads.mccme.ru/vmo/2026/iii-day1.pdf',
]
# Links from the public archive of the Moscow Center for Pedagogical Excellence.
# Keep provenance as an archive mirror when the file is hosted at tasks.olimpiada.ru.
from collect import parse_html
from urllib.parse import urljoin, urlparse
for source, item in pages.items():
    match = re.search(r'/activity/72/tasks/(20\d\d)\?class=10', source)
    if not match or item.get('status') != 'ok':
        continue
    start_year = int(match[1])
    root = parse_html((ROOT / item['path']).read_bytes())
    for a in root.xpath('//a[@href]'):
        target = urljoin(source, a.get('href'))
        if not target.lower().endswith('.pdf') or '-mun-' not in target:
            continue
        if not re.search(r'math-10(?:-11)?-', target):
            continue
        parent = next((x for x in a.iterancestors() if x.get('rname')), None)
        region = parent.get('rname') if parent is not None else 'Регион не указан'
        slugmatch = re.search(r'-mun-([a-z0-9_-]+?)-\d\d-\d\d', target)
        slug = slugmatch[1] if slugmatch else 'unknown'
        label = ' '.join(a.text_content().split())
        role = 'criteria' if 'Критер' in label else 'combined' if 'решения' in label.lower() and 'задания' in label.lower() else 'solutions' if 'Решен' in label else 'tasks'
        add({'url': target, 'text': label}, source_page=source, competition='vsosh',
            stage='municipal', year=start_year + 1, academic_year=f'{start_year}/{start_year + 1}',
            region=region, region_slug=slug, role=role,
            grade_scope=[10, 11] if 'math-10-11-' in target else [10],
            provenance='archive_mirror' if 'tasks.olimpiada.ru' in target else 'organizer')

# Exclude links that happened to contain the digits 10 in a size or in a year.
excluded = []
clean = []
for candidate in candidates:
    path = urlparse(candidate['url']).path.lower()
    wrong_grade = bool(re.search(r'/(?:usl|resh)[_-]?(?:0?[4-9]|11)(?:_|\.|-)', path))
    if 'usl_7-11' in path:
        wrong_grade = False
    wrong_grade = wrong_grade or path.endswith('usl_5-6.pdf')
    wrong_grade = wrong_grade or ('/zsfond.' in candidate['url'] and '/9-klass-' in path)
    if candidate['competition'] == 'vsosh' and candidate['stage'] == 'municipal' and wrong_grade:
        excluded.append(candidate)
    elif candidate['region_slug'] == 'sverdlovsk' and '/9-klass-' in path:
        excluded.append(candidate)
    elif path.endswith('/instr.pdf'):
        candidate['role'] = 'requirements'
        clean.append(candidate)
    else:
        clean.append(candidate)
candidates = clean
write_json(ROOT / 'data/excluded-links.json', excluded)
for candidate in candidates:
    if any(part in candidate['url'].lower() for part in [
        'pr-minpros', 'pr202-min', '/grafik/', 'p1091.pdf', 'attachments/',
    ]):
        candidate['role'] = 'regulations'
write_json(ROOT / 'data/candidates.json', candidates)
(ROOT / 'data/expanded-urls.txt').write_text('\n'.join(dict.fromkeys(urls)) + '\n')
print('Candidates:', len(candidates), 'URLs in this batch:', len(set(urls)))
