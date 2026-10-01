#!/usr/bin/env python3
"""Index grade 10 statements. PDFs remain authoritative for formulae/figures."""
import csv
import re
import subprocess
from collections import defaultdict
from collect import ROOT, read_json, write_json

TOPICS = {
    'geometry': ('Геометрия', r'треуголь|окружност|биссектрис|четырёхуголь|четырехуголь|касател|параллелограм|многоуголь|радиус|высот[ауы]|угол|вписан|описан|перпендикуляр|трапеци|прямоугольник|квадрат со сторон|квадрат сторон|круг\w* диамет|длины? отрезк|круглого озер'),
    'number_theory': ('Теория чисел', r'делит[ьс]|делится|делятся|делимость|делител|остат\w*|прост\w* чис|является простым|натуральн|цел\w* чис|цифр|взаимно прост|нацело|НОД|НОК|точн\w* квадрат|число оканчивается'),
    'combinatorics': ('Комбинаторика', r'клет|доск|домино|раскрас|покрас|фишк|шахмат|граф|вершин|реб[ерё]|команд|турнир|игра|игрок|ход\w*|петя|вася|пети|васи|плит|карточ|короб|шарик|разбил|разбито|разбиен|таблиц|множество|множества|выбрать|выбран|кажд\w* пар|лыжник|книг|ученик|обгон|жител|лжец|рыцар|рукопожат|марок|филателист|перелива|девочек|мальчик'),
    'algebra': ('Алгебра', r'трёхчлен|трехчлен|многочлен|корн|корень|уравнен|функци|квадратн|действительн|вещественн|положительн\w* чис|прогресс|последовательност|неравенств|произведени|сумм|выражени|рациональн|sin|cos|ctg|tg\(|скорост|бак\w* запол'),
}
METHODS = {
    'parity': ('Чётность', r'ч[её]тн'),
    'invariant': ('Инвариант', r'инвариант'),
    'monovariant': ('Моновариант', r'моно[вт]|уменьшается|возрастает'),
    'pigeonhole': ('Принцип Дирихле', r'дирихле'),
    'extremal': ('Крайний элемент', r'наименьш|наибольш|максимал|минимал|сам\w* (?:больш|мал|лев|прав)'),
    'double_counting': ('Двойной подсчёт', r'двойн\w* (?:подсч|сч[её]т)'),
    'induction': ('Индукция', r'индукц'),
    'construction': ('Конструкция', r'например|в качестве примера|построим|рассмотрим следующий пример'),
    'contradiction': ('От противного', r'противореч|предположим противное|допустим противное'),
    'bounds': ('Оценка', r'оценк|не меньше|не больше|не более|не менее'),
    'modular': ('Остатки', r'по модулю|остат\w*|сравнени\w* по'),
    'factorization': ('Разложение на множители', r'множител|разложени|разложим|факторизац'),
    'gcd': ('НОД и взаимная простота', r'взаимно прост|наибольш\w* общ\w* дел|НОД'),
    'valuations': ('Показатели простых', r'степен\w* прост|показател\w*|p-адич'),
    'graphs': ('Графовая модель', r'граф|р[её]бр|вершин\w* граф'),
    'strategy': ('Стратегия', r'стратег|выигрыш|выигра|проигра'),
    'angles': ('Углы и окружности', r'угол|окружност'),
    'similarity': ('Подобие', r'подобн|подобие'),
    'areas': ('Площади', r'площад'),
    'coordinates': ('Координаты и векторы', r'координат|вектор'),
    'vieta': ('Теорема Виета', r'виет'),
    'substitution': ('Подстановка', r'подстав|подстановка'),
    'symmetry': ('Симметрия', r'симметр'),
    'bijection': ('Соответствие и инъекция', r'биекц|инъекц|соответств'),
    'descent': ('Спуск', r'спуск'),
    'recurrence': ('Рекурсия', r'рекур|последовательност'),
    'matching': ('Паросочетания', r'паросочет'),
    'polynomials': ('Многочлены', r'многочлен|тр[её]хчлен'),
    'order': ('Упорядочивание', r'упорядоч|по возрастанию|по убыванию'),
    'projection': ('Проекции', r'проекц'),
    'information': ('Информация и различимость', r'информац|различим|вопрос'),
    'power': ('Степень точки', r'степен\w* точк|радикальн'),
}


def rawtext(d):
    path = ROOT / 'extracted/raw' / (d['id'] + '.txt')
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        subprocess.run(['pdftotext', '-raw', '-enc', 'UTF-8', str(ROOT / d['path']), str(path)], capture_output=True, check=True)
    text = path.read_text()
    # The 2019 collection's old embedded font maps CP1251 bytes to Latin-1.
    # Repair that character map without altering formula symbols.
    if len(re.findall(r'[\u00c0-\u00ff]', text)) > max(20, len(re.findall(r'[А-Яа-я]', text))):
        table = {n: bytes([n]).decode('cp1251') for n in range(0xc0, 0x100)}
        table.update({0xa8: 'Ё', 0xb8: 'ё'})
        text = text.translate(table)
    # Some older font mappings encode KOI8-R through Latin-1 and CP1251.
    if re.search(r'ЧУЕТПУУ|ТБУУ|НБФЕНБФ|ЛМБУУ|ЮФП',text,re.I):
        table={}
        for n in range(0xc0,0x100):
            table[ord(bytes([n]).decode('cp1251'))]=bytes([n]).decode('koi8-r')
        text=text.translate(table)
    text = text.replace('\f', '\n\f\n')
    return re.sub(r'(?m)^((?:Задача|Задание)\s*№?\s*(?:10\.)?\d+)\s*$', r'\1.', text)


def grade_slice(t, scope, grade=10):
    if scope == [10, 11]:
        return t, 0
    pattern = rf'(?m)^\s*(?:[IVX]+\s*этап\s*)?{grade}\s*(?:-?й\s*)?класс[^\n]*'
    matches=list(re.finditer(pattern,t,re.I))
    m=next((h for h in matches if not re.search(r'класс\s+\d+\s*$',h[0],re.I)),None)
    if not m:
        return (t,0)if scope==[10]else('',0)
    other = '|'.join(str(n) for n in range(4, 12) if n != grade)
    end = re.search(rf'(?m)^\s*(?:[IVX]+\s*этап\s*)?(?:{other})\s*(?:-?й\s*)?класс[^\n]*', t[m.end():], re.I)
    return t[m.end():m.end() + end.start()] if end else t[m.end():], m.end()


def parse(d):
    full = rawtext(d)
    if d['stage'] == 'regional':
        t, offset = full, 0
        pattern = r'(?m)^\s*(?:Задача\s+)?10[.](\d+)[.]\s*'
        all_pattern = r'(?m)^\s*(?:Задача\s+)?(?:9|10|11)[.]\d+[.]\s*'
    else:
        t, offset = grade_slice(full, d.get('grade_scope', [10]))
        pattern = r'(?m)^\s*(?:(?:Задача|Задание)\s*(?:№\s*)?|№\s*)?(?:10[.])?(\d{1,2})(?:[.)](?!\d)|(?=\s*\())\s*'
        all_pattern = pattern
        if d['stage']=='municipal':
            grade_pattern = r'(?m)^\s*(?:(?:Задача|Задание)\s*(?:№\s*)?)?10\.(\d{1,2})(?:[.)]|(?=\s))\s*'
            named_pattern = r'(?m)^\s*(?:(?:Задача|Задание)\s*(?:№\s*)?|№\s*)(\d{1,2})(?:[.)]|(?=\s*\())\s*'
            if len(re.findall(grade_pattern,t,re.I))>=2:
                pattern=all_pattern=grade_pattern
            elif len(re.findall(named_pattern,t,re.I))>=2:
                pattern=all_pattern=named_pattern
    numbered_variants = d['stage'] == 'municipal' and re.search(r'Вариант\s*10\.\d+\.\d+\.', t)
    if numbered_variants:
        pattern = r'(?m)^\s*(?:Задача\s+10\.(\d+)\.|Вариант\s*10\.(\d+)\.(\d+)\.)\s*'
        all_pattern = pattern
    marks = list(re.finditer(pattern, t, re.I))
    boundaries = [m.start() for m in re.finditer(all_pattern, t, re.I)] + [len(t)]
    out, seen = [], set()
    for m in marks:
        number = int(m[1] or m[2]) if numbered_variants else int(m[1])
        if not 1 <= number <= (6 if d['competition'] == 'mosh' else 10):
            continue
        preceding = t[:m.start()]
        variants = list(re.finditer(r'(?im)^\s*(?:10\s*класс\s*[(]?\s*)?(?:вариант\s*(?:№\s*)?([1-9АБВABC])|([1-9])\s*вариант)[.)]?\s*$', preceding)) if d['stage'] == 'municipal' else []
        variant = (m[3] or '1') if numbered_variants else (variants[-1][1] or variants[-1][2]) if variants else '1' if d.get('first_numbered_variant') else None
        key = number, variant
        if key in seen:
            continue
        end = next(b for b in boundaries if b > m.start())
        chunk = t[m.end():end].strip()
        body = re.split(r'(?im)^\s*(?:О?твет|Р?ешение(?:\s*\d+)?|Первое решение|Второе решение|Доказательство|Указание|Критерии|Система оценивания)[.:\s]', chunk, maxsplit=1)[0].strip()
        body=re.split(r'(?im)^\s*(?:Литература\s+\d+|Немецкий язык\s+\d+|Всероссийская олимпиада школьников по математике\s*$)',body,maxsplit=1)[0].strip()
        if re.match(r'Во время тура запрещ|В геометрических задачах допускается|При проверке оценивается|Задачи не обязательно|Все задачи равноценны|Решение математической задачи включает',body,re.I):
            continue
        if len(body) < 15 and d['role'] != 'solutions':
            continue
        seen.add(key)
        out.append(dict(number=number, variant=variant, statement_text=body,
                        solution_text=chunk[len(body):].strip(),
                        page=full[:offset + m.start()].count('\f') + 1))
    return out


def tags(text, rules):
    return [k for k, (_, pattern) in rules.items() if re.search(pattern, text, re.I)]


def book_solution(book, number, grade=10):
    full = rawtext(book)
    headers = list(re.finditer(rf'(?m)^\s*{grade}\s*класс[^\n]*', full))
    other = '|'.join(str(n) for n in range(8, 12) if n != grade)
    for header in headers:
        end = re.search(rf'(?m)^\s*(?:{other})\s*класс[^\n]*', full[header.end():])
        stop = header.end() + end.start() if end else len(full)
        section = full[header.end():stop]
        marks = list(re.finditer(r'(?m)^\s*(?:Задача\s*)?(\d+)[.]\s*', section))
        for j, mark in enumerate(marks):
            if int(mark[1]) != number:
                continue
            finish = marks[j+1].start() if j+1 < len(marks) else len(section)
            chunk = section[mark.end():finish].strip()
            cross = re.match(r'См\.\s*(?:решение\s*)?задач[уи]\s*(\d+)\s*для\s*(\d+)\s*класса', chunk, re.I)
            if cross:
                return book_solution(book, int(cross[1]), int(cross[2]))
            if not re.search(r'Ответ|Решение|решение', chunk):
                continue
            return chunk, full[:header.end()+mark.start()].count('\f')+1
    return None


def main():
    docs = read_json(ROOT / 'data/documents.json', [])
    annotations = read_json(ROOT / 'data/annotations.json', {})
    groups = defaultdict(list)
    for d in docs:
        if d['role'] not in ['tasks', 'combined', 'solutions', 'criteria'] or d['extraction_status'] != 'text':
            continue
        if d['stage'] == 'regional':
            key = (d['competition'], d['stage'], d['year'], 'federal')
        else:
            key = (d['competition'], d['stage'], d['year'], d['region_slug'])
        groups[key].append(d)
    tasks, gaps = {}, []
    for key, group in sorted(groups.items()):
        # Prefer the official collection with solutions for federal tasks; prefer
        # separate condition sheets elsewhere. Register all alternate sources.
        group.sort(key=lambda d: (
            d['region_slug'] != 'moscow' if d['stage'] == 'regional' else False,
            ('resh' not in d['url']) if d['stage'] == 'regional' and d['year'] == 2010 else False,
            d['role'] != 'combined' if d['stage'] == 'regional' else d['role'] != 'tasks',
            'var10' not in d['url'] if d['competition'] == 'mosh' else False,
            -d['bytes'], d['url']))
        if key[1] == 'municipal' and any(re.search(r'Вариант\s*10\.\d+\.\d+\.', rawtext(d)) for d in group):
            for d in group:
                d['first_numbered_variant'] = True
        before = len(tasks)
        condition_positions = {(r['number'],r['variant'])for d in group if d['role']in ['tasks','combined']for r in parse(d)}
        for d in group:
            parsed = parse(d)
            for row in parsed:
                if d['stage'] == 'regional':
                    task_id = f"R-{d['year']}-10.{row['number']}"
                elif d['competition'] == 'mosh':
                    task_id = f"MOSH-{d['year']}-10.{row['number']}"
                else:
                    task_id = f"M-{d['academic_year'].replace('/', '-')}-{d['region_slug']}-10.{row['number']}"
                if row['variant']:
                    task_id += '-v' + row['variant']
                reference = dict(document_id=d['id'], path=d['path'], page=row['page'],
                                 url=d['url'], role=d['role'], region=d['region'],
                                 bundle_member=d.get('bundle_member'))
                if task_id in tasks:
                    tasks[task_id]['sources'].append(reference)
                    if row['solution_text'] and not tasks[task_id]['solution_text']:
                        tasks[task_id]['solution_text'] = row['solution_text']
                    continue
                if len(row['statement_text'])<15 or d['role'] == 'criteria':
                    continue
                if d['stage']=='municipal' and d['role']=='solutions' and len(condition_positions)>=3 and (row['number'],row['variant'])not in condition_positions:
                    continue
                task = dict(row, id=task_id, competition=d['competition'], stage=d['stage'],
                            year=d['year'], academic_year=d['academic_year'], grade=10,
                            grade_scope=d.get('grade_scope'),
                            region='Федеральный комплект' if d['stage'] == 'regional' else d['region'],
                            region_slug=key[3], sources=[reference],
                            topics=tags(row['statement_text'], TOPICS),
                            methods=tags(row['statement_text'] + '\n' + row['solution_text'], METHODS),
                            review_status='automatic',
                            reserve=d['year'] == 2026 and d['stage'] in ['regional', 'main'])
                if not task['topics']:
                    task['topics'] = ['unclassified']
                task.update(annotations.get(task_id, {}))
                tasks[task_id] = task
        if len(tasks) == before:
            gaps.append(dict(competition=key[0], stage=key[1], year=key[2], region_slug=key[3],
                             reason='Numbering not recognized', document_ids=[d['id'] for d in group]))
    out = sorted(tasks.values(), key=lambda t: (t['competition'], t['stage'], -t['year'], t['region_slug'], t['variant'] or '', t['number']))
    for task in out:
        cross = re.match(r'См\.\s*задачу\s*(\d+)\s*для\s*(\d+)\s*класса', task['statement_text'], re.I)
        if not cross or task['competition'] != 'mosh':
            continue
        num, grade = map(int, cross.groups())
        books = [d for d in docs if d['competition'] == 'mosh' and d['year'] == task['year'] and re.search(r'/\d+mmo\.pdf$', d['url'])]
        for book in books:
            full = rawtext(book)
            sliced, offset = grade_slice(full, [8, 9, 10, 11], grade)
            markers = list(re.finditer(r'(?m)^\s*(?:Задача\s*)?(\d+)[.]\s*', sliced))
            match = next((m for m in markers if int(m[1]) == num), None)
            if not match:
                continue
            end = next((m.start() for m in markers if m.start() > match.start()), len(sliced))
            task['cross_reference'] = dict(grade=grade, number=num, original=task['statement_text'])
            task['statement_text'] = sliced[match.end():end].strip()
            task['sources'].insert(0, dict(document_id=book['id'], path=book['path'],
                page=full[:offset+match.start()].count('\f')+1, url=book['url'],
                role='shared_statement', region=book['region'], bundle_member=None))
            if task['review_status'] == 'automatic':
                task['topics'] = tags(task['statement_text'], TOPICS) or ['unclassified']
            break
    for task in out:
        if task['competition'] != 'mosh' or task['solution_text']:
            continue
        books = [d for d in docs if d['competition'] == 'mosh' and d['year'] == task['year'] and re.search(r'/\d+mmo\.pdf$', d['url'])]
        for book in books:
            found = book_solution(book, task['number'])
            if found:
                task['solution_text'], page = found
                task['sources'].append(dict(document_id=book['id'], path=book['path'], page=page,
                    url=book['url'], role='solutions', region=book['region'], bundle_member=None))
                break
    write_json(ROOT / 'data/tasks.json', out)
    write_json(ROOT / 'data/extraction-gaps.json', gaps)
    write_json(ROOT / 'data/taxonomy.json', {'topics': {k: v[0] for k, v in TOPICS.items()}, 'methods': {k: v[0] for k, v in METHODS.items()}})
    with (ROOT / 'data/tasks.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'competition', 'stage', 'academic_year', 'region', 'variant', 'number', 'topics', 'methods', 'review_status', 'summary', 'pdf', 'page', 'source_url'])
        for t in out:
            s = t['sources'][0]
            writer.writerow([t['id'], t['competition'], t['stage'], t['academic_year'], t['region'], t['variant'], t['number'], ';'.join(t['topics']), ';'.join(t['methods']), t['review_status'], t.get('summary', ''), s['path'], s['page'], s['url']])
    print('Indexed tasks:', len(out), 'Groups requiring reading:', len(gaps))
    for comp, stage in [('vsosh', 'regional'), ('mosh', 'main')]:
        print(comp, stage, {y: sum(t['year'] == y and t['competition'] == comp and t['stage'] == stage for t in out) for y in range(2010, 2027)})


if __name__ == '__main__':
    main()
