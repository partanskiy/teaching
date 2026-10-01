#!/usr/bin/env python3
"""Verify that submission and working plans share metadata and all 34 lessons."""
import argparse
import json
import re
import subprocess
import xml.etree.ElementTree as E
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def require(condition,message):
    if not condition:raise AssertionError(message)


def doc(path):
    with zipfile.ZipFile(path)as z:
        root=E.fromstring(z.read('word/document.xml'))
    return root,'\n'.join(''.join(p.itertext())for p in root.findall('.//w:p',NS))


def normal(text):return ' '.join(text.split())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-only',action='store_true')
    parser.add_argument('--submission-only',action='store_true')
    parser.add_argument('--without-pdf',action='store_true')
    parser.add_argument('--rebuilt-submission',type=Path,help='Compare checked-out submission contents with a fresh build, ignoring creation timestamps')
    args=parser.parse_args()
    program=json.loads((ROOT/'data/program.json').read_text());lessons=json.loads((ROOT/'data/lessons.json').read_text())
    require(len(lessons)==program['expected_lessons']==34,'Programme must contain 34 lessons')
    require([l['number']for l in lessons]==list(range(1,35)),'Lesson order differs')
    require(all(l['minutes']==program['lesson_minutes']==90 and l['academic_hours']==2 for l in lessons),'Lesson duration differs')
    require(all(l['block']in program['blocks']for l in lessons),'Unknown programme section')
    tasks={t['id']for t in json.loads((ROOT/'data/tasks.json').read_text())}
    require(all(i in tasks for l in lessons for i in l['classroom']+l['homework']),'Missing working task')
    for path,prefix in [('course/plan.md','## Занятие '),('course/print-plan.md','## ')]:
        text=(ROOT/path).read_text()
        require(program['author']in text and program['academic_year']in text,'Working plan metadata differs: '+path)
        positions=[]
        for l in lessons:
            marker=prefix+str(l['number'])+' '+l['title']+'\n'
            require(marker in text,'Missing working lesson: '+marker)
            positions.append(text.index(marker))
            require(l['goal']in text,'Working goal differs: '+str(l['number']))
        require(positions==sorted(positions),'Working lesson order differs')
    if not args.source_only:
        formal_root,formal_text=doc(ROOT/'course/План_для_сдачи_2026-2027.docx')
        require(program['author']in formal_text and program['academic_year']in formal_text,'Submission metadata differs')
        rows=[]
        for row in formal_root.findall('.//w:tbl/w:tr',NS):
            cells=[''.join(c.itertext())for c in row.findall('w:tc',NS)]
            if cells and cells[0].isdigit():rows.append(cells)
        require(len(rows)==34,'Submission must contain 34 calendar rows')
        for row,l in zip(rows,lessons):
            require(row==[str(l['number']),l['month'],l['title'],str(l['academic_hours']),l['goal']],
                    'Submission row differs: '+str(l['number']))
        for text in ['/home/','file://','olympiad-math','репозитор','локальн','R-20','MOSH-20','.docx','.pdf']:
            require(text not in formal_text,'Internal reference in submission: '+text)
        require(not formal_root.findall('.//w:hyperlink',NS),'Submission contains a hyperlink')
        with zipfile.ZipFile(ROOT/'course/План_для_сдачи_2026-2027.docx')as z:
            styles=E.fromstring(z.read('word/styles.xml'))
            if args.rebuilt_submission:
                with zipfile.ZipFile(args.rebuilt_submission)as rebuilt:
                    require(set(z.namelist())==set(rebuilt.namelist()),'Rebuilt submission package differs')
                    for name in z.namelist():
                        if name!='docProps/core.xml':
                            require(z.read(name)==rebuilt.read(name),'Stale submission contents: '+name)
        fonts=styles.findall('.//w:rFonts',NS)
        require(any(x.get('{'+NS['w']+'}ascii')=='Times New Roman'for x in fonts),'Submission font differs')
        mapping=json.loads((ROOT/'data/submission-map.json').read_text())
        require(mapping['academic_hours']==68 and mapping['clock_minutes']==3060,'Submission hours differ')
        require(mapping['lessons']==[{k:l[k]for k in ['number','month','title','minutes','academic_hours','goal','block']}for l in lessons],
                'Submission mapping differs')
        if not args.submission_only:
            _,working_text=doc(ROOT/'course/План_34_занятия_2026-2027.docx')
            require(program['author']in working_text and program['academic_year']in working_text,'Working Word metadata differs')
            for l in lessons:require(str(l['number'])+' '+l['title']in working_text,'Working Word lesson differs')
            if not args.without_pdf:
                for name in ['План_для_сдачи_2026-2027','План_34_занятия_2026-2027']:
                    result=subprocess.run(['pdftotext','-raw',str(ROOT/'course'/(name+'.pdf')),'-'],text=True,capture_output=True,check=True)
                    text=normal(result.stdout)
                    require(program['author']in text and program['academic_year']in text,'PDF metadata differs')
                    for l in lessons:require(l['title']in text,'PDF lesson differs: '+str(l['number']))
    print('Plans synchronized: 34 lessons, identical order, topics, goals, author, year and 68 academic hours.')


if __name__=='__main__':main()
