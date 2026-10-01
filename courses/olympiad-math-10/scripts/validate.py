#!/usr/bin/env python3
"""Check the delivered archive, source links, curriculum and printed plan."""
import hashlib
import json
import re
import subprocess
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit
from lxml import etree
from collect import ROOT, read_json, write_json


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    docs = read_json(ROOT/'data/documents.json',[])
    tasks = read_json(ROOT/'data/tasks.json',[])
    lessons = read_json(ROOT/'data/lessons.json',[])
    doc_by_id = {d['id']:d for d in docs}
    by_id = {t['id']:t for t in tasks}
    require(len(doc_by_id)==len(docs),'Duplicate document IDs')
    require(len(by_id)==len(tasks),'Duplicate task IDs')
    for d in docs:
        p=ROOT/d['path']; content=p.read_bytes()
        require(p.resolve().is_relative_to(ROOT.resolve()),'Path outside project: '+d['path'])
        require(content.startswith(b'%PDF') if p.suffix=='.pdf' else zipfile.is_zipfile(p),'Invalid file signature: '+d['id'])
        require(len(content)==d['bytes'],'File size changed: '+d['id'])
        require(hashlib.sha256(content).hexdigest()==d['sha256'],'SHA256 changed: '+d['id'])
        require(10 in d['grade_scope'],'Document excluded from grade 10: '+d['id'])
        require((ROOT/d['text_path']).is_file(),'Missing extraction: '+d['id'])
        require(d.get('retrieved_at') and d.get('source_page') and d.get('url'),'Missing provenance: '+d['id'])
    expected_paths={d['path']for d in docs}
    archive_paths={str(p.relative_to(ROOT))for p in (ROOT/'archive').rglob('*')if p.is_file()}
    require(archive_paths==expected_paths,'Archive files do not match manifest')
    for t in tasks:
        require(t['grade']==10,'Task has wrong grade: '+t['id'])
        require(bool(t['statement_text'].strip()),'Empty statement: '+t['id'])
        require(t['sources'],'No sources: '+t['id'])
        for s in t['sources']:
            require(s['document_id']in doc_by_id,'Unknown source document: '+t['id'])
            d=doc_by_id[s['document_id']]
            require(s['path']==d['path'],'Incorrect source path: '+t['id'])
            require(s['page']>=1 and (d['text_pages']is None or s['page']<=d['text_pages']),'PDF page outside document: '+t['id'])
        if t['review_status']!='automatic':
            require(t.get('summary') and t['topics'] and 'unclassified' not in t['topics'],'Incomplete manual annotation: '+t['id'])
        if t['review_status']=='solution_reviewed':
            require(t.get('solution_key'),'Missing reviewed solution key: '+t['id'])
    for year in range(2010,2027):
        expected=set(range(1,9 if year<=2017 else 11))
        actual={t['number']for t in tasks if t['stage']=='regional' and t['year']==year}
        require(actual==expected,'Incomplete regional year: '+str(year))
    for year in range(2011,2027):
        actual={t['number']for t in tasks if t['competition']=='mosh' and t['year']==year}
        require(actual==set(range(1,7)),'Incomplete MOSH year: '+str(year))
    core=[t for t in tasks if t['stage']in ['regional','main']]
    require(len(core)==250 and all(t['review_status']!='automatic'for t in core),'Core annotations incomplete')
    require([l['number']for l in lessons]==list(range(1,35)),'Expected exactly 34 ordered lessons')
    require(sum(l['minutes']for l in lessons)==3060,'Expected 51 clock hours')
    require(sum(l['academic_hours']for l in lessons)==68,'Expected 68 academic hours')
    for l in lessons:
        require(l['minutes']==90,'Wrong duration: '+str(l['number']))
        for task_id in l['classroom']+l['homework']:
            require(task_id in by_id,'Course references missing task: '+task_id)
        if l['block'] not in ['assessment','proof']:
            require(all(by_id[i]['review_status']=='solution_reviewed'for i in l['classroom']),'Main solution not checked: '+str(l['number']))
    controls={i:l['number']for l in lessons if l['number']in [11,17,18,25,33]for i in l['classroom']+(l['homework']if l['number']==11 else [])}
    require(set(controls)=={t['id']for t in tasks if t['reserve']},'Incorrect reserve set')
    for l in lessons:
        for task_id in l['classroom']+l['homework']:
            require(task_id not in controls or l['number']>=controls[task_id],'Reserve issued too early: '+task_id)
    missing_links=[]
    for p in [ROOT/'README.md',ROOT/'index.html',*(ROOT/'research').glob('*.md'),*(ROOT/'course').glob('*.md')]:
        text=p.read_text()
        references=re.findall(r'\]\(([^)]+)\)',text)if p.suffix=='.md'else re.findall(r'(?:href|src)="([^"]+)"',text)
        for ref in references:
            if urlsplit(ref).scheme or ref.startswith('#'):continue
            local=(p.parent/unquote(ref.split('#')[0])).resolve()
            if not local.exists():missing_links.append((str(p.relative_to(ROOT)),ref))
    require(not missing_links,'Missing local links: '+repr(missing_links))
    printed=ROOT/'course/План_34_занятия_2026-2027.docx'
    with zipfile.ZipFile(printed)as z:
        xml=etree.fromstring(z.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text='\n'.join(''.join(p.xpath('.//w:t/text()',namespaces=ns))for p in xml.xpath('//w:p',namespaces=ns))
    require('Партанский Илья Михайлович'in text and '2026/2027'in text,'Wrong author or season in Word plan')
    for l in lessons:
        require(str(l['number'])+' '+l['title']in text,'Lesson missing in Word: '+str(l['number']))
    require(not any(c in text for c in '\u2013\u2014\u2018\u2019\u201c\u201d\u00ab\u00bb'),'Unwanted decorative punctuation in Word')
    pdf=ROOT/'course/План_34_занятия_2026-2027.pdf'
    pdftext=subprocess.run(['pdftotext','-layout',str(pdf),'-'],capture_output=True,text=True,check=True).stdout
    for task_id in {i for l in lessons for i in l['classroom']+l['homework']}:
        require(task_id in pdftext,'Task missing in printed PDF: '+task_id)
    result=dict(status='passed',date='2026-10-01',documents_checked=len(docs),
        unique_sha256=len({d['sha256']for d in docs}),task_links_checked=sum(len(t['sources'])for t in tasks),
        regional_tasks=154,mosh_tasks=96,reviewed_statements=sum(t['review_status']!='automatic'for t in tasks),
        reviewed_solutions=sum(t['review_status']=='solution_reviewed'for t in tasks),lessons=34,
        academic_hours=68,clock_hours=51,reserve_tasks=len(controls),
        download_failures=len(read_json(ROOT/'data/download-failures.json',[])),
        extraction_gaps=len(read_json(ROOT/'data/extraction-gaps.json',[])),
        note='Integrity and coverage checks; automatic municipal topic labels remain provisional.')
    write_json(ROOT/'data/validation.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
