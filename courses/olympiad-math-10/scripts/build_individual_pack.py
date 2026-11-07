#!/usr/bin/env python3
"""Build exactly two self-contained Typst sources and their PDF books."""
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'course/individual/municipal-10-2026'
DATA = ROOT/'data/individual-municipal-10-2026.json'


def quote(s):
    return json.dumps(s, ensure_ascii=False)


def info(path):
    output = subprocess.check_output(['pdfinfo', '-box', str(path)], text=True)
    pages = int(re.search(r'Pages:\s+(\d+)', output).group(1))
    box = re.search(r'Page size:\s+([\d.]+) x ([\d.]+)', output)
    return pages, float(box.group(1)), float(box.group(2))


PREAMBLE = '''// Self-contained source, Typst 0.15.1 or newer.
// Official PDF pages are embedded as bytes to preserve formulas, figures,
// searchable text and source typography. No external files are required.
// Edit the native introductory text and the sequence of embedded pages here.
#set page(paper: "a4", margin: (x: 13mm, top: 17mm, bottom: 15mm),
  header: align(right, text(size: 8pt)[ВсОШ. Математика. Муниципальный этап. 10 класс]),
  footer: align(center, context counter(page).display()))
#set text(font: "Times New Roman", size: 10.5pt, lang: "ru")
#set par(justify: true, leading: 0.45em)
#set heading(numbering: none)
#let decode(hex) = bytes(hex.matches(regex("..")).map(m => int(m.text, base: 16)))
#let original(data, page, title, source: "") = {
  pagebreak()
  text(size: 10pt, weight: "bold", title)
  linebreak()
  if source != "" { text(size: 7.5pt, link(source)[Оригинальная публикация]); linebreak() }
  v(2mm)
  align(center, image(data, format: "pdf", page: page,
    width: 184mm, height: 248mm, fit: "contain"))
}
'''


def embedded(index, path, document_id):
    raw = path.read_bytes()
    h = raw.hex()
    # Adjacent string chunks keep each source line short without data files.
    chunks = '\n'.join('  '+quote(h[i:i+192])+',' for i in range(0,len(h),192))
    return (f'// Embedded document {document_id}; SHA-256 {hashlib.sha256(raw).hexdigest()}\n'
            f'#let pdf{index} = decode((\n{chunks}\n).join())\n')


def main():
    data = json.loads(DATA.read_text())
    creation_timestamp = str(int(datetime.fromisoformat(data['created_on']).replace(tzinfo=timezone.utc).timestamp()))
    records = {x['file']:x for x in data['files']}
    docs = {d['id']:d for d in json.loads((ROOT/'data/documents.json').read_text())}
    tasks = {t['id']:t for t in json.loads((ROOT/'data/tasks.json').read_text())}
    for record in data['files']:
        d = docs[record['document_id']]
        assert hashlib.sha256((ROOT/d['path']).read_bytes()).hexdigest()==d['sha256']
    for mock in data['mocks']:
        assert len(mock['task_ids'])==mock['tasks']
        assert not any(tasks[t]['reserve'] for t in mock['task_ids'])
    assert not any(tasks[t['task_id']]['reserve'] for t in data['thematic'])

    with tempfile.TemporaryDirectory(prefix='municipal-books-') as directory:
        tmp = Path(directory)
        def extract(relative, crop=False):
            record = records[relative]
            src = ROOT/docs[record['document_id']]['path']
            selected = record['pages_selected']
            if selected == 'all' and not crop:
                return src
            page = selected[0]
            dst = tmp/(record['document_id']+'.pdf')
            subprocess.run(['pdfseparate','-f',str(page),'-l',str(page),str(src),str(tmp/'page-%d.pdf')],check=True)
            shutil.move(tmp/f'page-{page}.pdf',dst)
            # pdfseparate creates a fresh trailer ID even for identical pages.
            # Normalize rotation and volatile metadata before embedding bytes.
            normalized = tmp/(record['document_id']+'-normalized.pdf')
            subprocess.run(['gs','-q','-dSAFER','-dBATCH','-dNOPAUSE',
                '-dOmitInfoDate=true','-dOmitID=true','-dOmitXMP=true',
                '-sDEVICE=pdfwrite','-dAutoRotatePages=/None',
                '-sOutputFile='+str(normalized),str(dst)],check=True)
            dst = normalized
            if crop:
                _,width,height=info(dst)
                cropped = tmp/(record['document_id']+'-single.pdf')
                subprocess.run(['gs','-q','-dSAFER','-dBATCH','-dNOPAUSE',
                    '-dOmitInfoDate=true','-dOmitID=true','-dOmitXMP=true',
                    '-sDEVICE=pdfwrite','-dAutoRotatePages=/None','-dFIXEDMEDIA',
                    f'-dDEVICEWIDTHPOINTS={width/2}',f'-dDEVICEHEIGHTPOINTS={height}',
                    '-sOutputFile='+str(cropped),str(dst)],check=True)
                dst = cropped
            return dst

        base = tmp/'moscow-2025-main.pdf'
        subprocess.run(['typst','compile','--creation-timestamp',creation_timestamp,'--root',str(ROOT),
            str(ROOT/'research/municipal-pack-2026-moscow-2025.typ'),str(base)],check=True)
        task_entries=[]; solution_entries=[]
        for i,mock in enumerate(data['mocks'],1):
            src = base if mock['code']=='05-moscow-2025' else extract(
                mock['conditions'],crop=mock['code'] in ['02-moscow-2017','03-moscow-2018'])
            record = records['extras/moscow-2025-all-versions.pdf'] if mock['code']=='05-moscow-2025' else records[mock['conditions']]
            task_entries.append((src,record,f'Пробник {i}. '+mock['title']))
            solution_entries.append((extract(mock['solutions']),records[mock['solutions']],f'Пробник {i}. '+mock['title']))
        theme_titles={'N25':'Новосибирская область, 2025/2026','T24':'Татарстан, 2024/2025',
                      'M25':'Московская область, 2025/2026','T25':'Татарстан, 2025/2026'}
        for code,title in theme_titles.items():
            r=f'thematic/{code}-tasks.pdf'; s=f'solutions/{code}-solutions.pdf'
            task_entries.append((extract(r),records[r],code+'. '+title))
            solution_entries.append((extract(s),records[s],code+'. '+title))
        extra = records['extras/moscow-2025-all-versions.pdf']
        task_entries.append((extract(extra['file']),extra,'Приложение. Москва 2025/2026, все версии задач'))

        common = '''= ВсОШ. Муниципальный этап. Математика. 10 класс
Комплект подготовки для Москвы. Составлен 31 октября 2026 года.

Семь полных тренировочных комплектов: пять московских и два запасных из других регионов, всего 44 задачи. Тематическая часть содержит ещё 20 задач. Дополнительные версии московских задач 2025 года сохранены в приложении. Они не являются независимыми полными пробниками.

Комплект состоит ровно из четырёх файлов: tasks.typ, tasks.pdf, solutions.typ, solutions.pdf. Оба исходника Typst самодостаточны. Официальные страницы встроены внутрь, формулы и рисунки сохранены в исходной вёрстке; редактирование вводных страниц и порядка материалов выполняется в Typst. Для изменения текста на оригинальной странице требуется редактировать её исходник.

Тур для 10-11 классов Москвы назначен на 4 декабря 2026 года, 16:00. Проверено 31 октября по #link("https://vos.olimpiada.ru/subject/math")[официальному расписанию]. Длительность и организационные инструкции уточнить перед туром. Региональные комплекты не заменяют московскую специфику, а расширяют набор методов.
'''
        guide = '''
== Как работать
Начать с пробника 1, Москва 2024/25. Написать самостоятельную попытку, затем открыть соответствующий раздел solutions.pdf. Для первой диагностики можно выбрать 120 минут и отдельно отметить, что удалось доделать позже. Исторические московские туры 2017-2019 годов рассчитаны на 240 минут; их исходная длительность не является регламентом тура 2026 года.

Записывать дату, время, полностью решённые номера, частичные продвижения и причину каждой ошибки. Через 2-3 дня восстановить неудавшееся доказательство без решения. Между пробниками брать задачи из двух слабых тем; на одну попытку выделять 20-40 минут.

#table(columns: (29mm, 45mm, 1fr), inset: 4pt, align: left,
 [*Неделя*],[*Пробник*],[*Самостоятельная работа*],
 [31.10-06.11],[1. Москва 2024/25],[4 тематические задачи и разбор ошибок.],
 [07.11-13.11],[2. Москва 2017/18],[4 тематические задачи; комбинаторика и запись доказательства.],
 [14.11-20.11],[3. Москва 2018/19],[4 тематические задачи, в том числе геометрия.],
 [21.11-27.11],[4. Москва 2019/20],[4 тематические задачи и повторение ошибок.],
 [28.11-03.12],[5. Москва 2025/26],[Оставшиеся 4 тематические задачи; завершить пробник за несколько дней до тура.],
)

Пробники 6 и 7 - запасные. Задачи тематической части не входят в эти семь пробников. N25.2 уже была в кружке 24 октября: её использовать как письменное повторение. Контрольный резерв общего курса не включён.

При нехватке времени сохранить диагностику 2024 года, итоговый пробник 2025 года и работу над ошибками между ними. Баллы разных лет считать по соответствующим критериям, не назначать всем задачам автоматически по 7 баллов.

#pagebreak()
= Указатель комплектов
'''
        for i,mock in enumerate(data['mocks'],1):
            guide += f'{i}. {mock["title"]}: {mock["tasks"]} задач.\n\n'
        guide+='''
Комплект 5 - учебная сборка основных версий задач официального московского комплекта. Не утверждается, что именно эта комбинация выдавалась конкретному участнику. В приложении приведены все версии; основная версия там повторяется. Решения основной и дополнительных версий находятся в разделе 5 книги solutions.pdf.

В старых оригиналах 2017 и 2018 годов было по две одинаковые копии рядом. Для этой книги оставлена одна копия каждого условия. Оригиналы остальных комплектов сохранены полностью, включая рисунки.

== Тематический указатель
Код означает раздел и номер в официальном листке: N25.1 - задача 1 раздела N25. Секции двух книг совпадают. N25 - Новосибирская область 2025/26; T24 - Татарстан 2024/25; M25 - Московская область 2025/26; T25 - Татарстан 2025/26.

#table(columns: (18mm, 31mm, 1fr), inset: 3pt, align: left,
 [*Код*],[*Раздел*],[*Метод*],
'''
        for t in data['thematic']:
            guide+=f' [{t["code"]}],[{t["topic"]}],[{t["focus"]}],\n'
        guide+=')\n'
        solutions_intro='''
= Официальные решения
В этой книге собраны все решения семи пробников и двадцати тематических задач. Разделы и исходные номера совпадают с tasks.pdf. В разделе 5 находятся также официальные разборы и ответы дополнительных версий московских задач 2025 года.

Сначала сделать самостоятельную попытку. При разборе отдельно проверить полноту оценки, наличие примера, рассмотрение всех случаев и запись доказательства. После чтения закрыть решение и восстановить его самостоятельно.

Тексты официальных страниц не перепечатаны из OCR: сохранены исходные формулы, рисунки и критерии. Некоторые официальные решения повторяют условие; это оставлено для удобства. Источник каждого раздела указан над страницей.
'''
        generated={}
        for kind,entries,intro in [('tasks',task_entries,common+guide),('solutions',solution_entries,solutions_intro)]:
            lines=[PREAMBLE,intro]
            for index,(path,record,title) in enumerate(entries):
                lines.append(embedded(index,path,record['document_id']))
                count,_,_=info(path)
                for page in range(1,count+1):
                    lines.append(f'#original(pdf{index}, {page}, {quote(title+f". Страница {page}/{count}")}, source: {quote(record["source_url"])})\n')
            src=tmp/(kind+'.typ');src.write_text('\n'.join(lines))
            pdf=tmp/(kind+'.pdf')
            subprocess.run(['typst','compile','--creation-timestamp',creation_timestamp,'--root',str(tmp),str(src),str(pdf)],check=True)
            generated[kind]=(src,pdf)

        if (OUTPUT/'manifest.json').exists():
            archive=ROOT/'research/build/municipal-10-2026-legacy'
            archive.parent.mkdir(parents=True,exist_ok=True)
            if archive.exists():
                raise RuntimeError('Legacy archive already exists; refusing to overwrite')
            shutil.move(OUTPUT,archive)
        OUTPUT.mkdir(parents=True,exist_ok=True)
        expected={f'{kind}.{ext}' for kind in generated for ext in ['typ','pdf']}
        if {p.name for p in OUTPUT.iterdir()}-expected:
            raise RuntimeError('Unexpected files in four-file delivery directory')
        for kind,(src,pdf) in generated.items():
            shutil.copyfile(src,OUTPUT/src.name);shutil.copyfile(pdf,OUTPUT/pdf.name)
        assert {p.name for p in OUTPUT.iterdir()}==expected
        archive=Path.home()/'Downloads/ВсОШ_математика_10_муниципальный_подготовка_2026.zip'
        archive.parent.mkdir(parents=True,exist_ok=True)
        with ZipFile(archive,'w',ZIP_DEFLATED) as z:
            for name in sorted(expected):z.write(OUTPUT/name,name)
        print('Delivered exactly four files:',OUTPUT)
        for name in sorted(expected):print(name,(OUTPUT/name).stat().st_size)
        print('ZIP:',archive)


if __name__=='__main__':
    main()
