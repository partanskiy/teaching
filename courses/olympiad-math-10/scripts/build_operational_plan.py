#!/usr/bin/env python3
"""Link a realistic session calendar to the shared annual programme and tasks."""
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / 'data' / name).read_text())


def display(value):
    return date.fromisoformat(value).strftime('%d.%m.%Y')


def main():
    plan = read('operational-plan.json')
    lessons = {lesson['number']: lesson for lesson in read('lessons.json')}
    tasks = {task['id']: task for task in read('tasks.json')}
    start = date.fromisoformat(plan['first_regular_session'])
    end = date.fromisoformat(plan['last_regular_saturday'])
    holidays = [(date.fromisoformat(p['start']), date.fromisoformat(p['end']))
                for p in plan['holiday_periods']]
    saturdays = []
    current = start
    while current <= end:
        if current.weekday() != 5:
            raise ValueError('The calendar must start on a Saturday')
        saturdays.append(current)
        current += timedelta(days=7)
    blocked = [d for d in saturdays if any(a <= d <= b for a, b in holidays)]
    battles = {date.fromisoformat(d) for d in plan['mathematical_battle_dates']}
    other_cancelled = {date.fromisoformat(d) for d in plan['other_cancelled_dates']}
    cancellations = (battles | other_cancelled) & set(saturdays)
    available = [d for d in saturdays if d not in blocked and d not in cancellations]
    slots = plan['slots']
    if [date.fromisoformat(s['date']) for s in slots] != available:
        raise ValueError('Candidate dates must match Saturdays outside holidays and known cancellations')
    if any(s['module'] not in lessons for s in slots):
        raise ValueError('Unknown programme module')
    if any(s['priority'] not in ['core', 'milestone', 'buffer'] for s in slots):
        raise ValueError('Unknown session priority')
    prepared_sessions = {}
    for slot in slots:
        if not slot.get('session_file'):
            continue
        session = json.loads((ROOT / slot['session_file']).read_text())
        if session['date'] != slot['date'] or session['minutes'] != lessons[slot['module']]['minutes']:
            raise ValueError('Prepared session date or duration differs from the calendar')
        selected = session['tasks']
        if len({item['id'] for item in selected}) != len(selected):
            raise ValueError('Prepared session tasks must be distinct')
        if [item['number'] for item in selected] != list(range(1, len(selected) + 1)):
            raise ValueError('Prepared session task numbers must be consecutive')
        if set(session['programme_modules']) != {item['programme_module'] for item in selected}:
            raise ValueError('Prepared session module list differs from its tasks')
        for item in selected:
            lesson = lessons[item['programme_module']]
            if tasks[item['id']]['reserve'] or item['id'] not in lesson['classroom'] + lesson['homework']:
                raise ValueError('Prepared session task must belong to its module and not be reserved')
        prepared_sessions[slot['date']] = session
    core = [s for s in slots if s['priority'] != 'buffer']
    remaining_battles = max(plan['mathematical_battle_saturdays_estimate']
                            - len(battles & set(saturdays)), 0)
    capacity = len(available) - remaining_battles
    if len(core) > capacity:
        raise ValueError('The core sequence exceeds the estimated capacity; reduce or move sessions')
    calendar = read('calendar.json')
    module_dates = {s['module']: date.fromisoformat(s['date']) for s in slots}
    for constraint in plan['preparation_constraints']:
        event = next(e for e in calendar['events'] if e['event'] == constraint['event']
                     and e['region'] == constraint['region'])
        if event['status'] == 'published' and event.get('date'):
            deadline = date.fromisoformat(event['date'])
            late = [m for m in constraint['modules'] if module_dates[m] >= deadline]
            if late:
                raise ValueError(f"Preparation for {event['event']} must finish before {deadline}; "
                                 f"move modules {late}")

    def problem(task_id, solutions=False):
        t = tasks[task_id]
        roles = ['solutions', 'criteria', 'combined'] if solutions else ['tasks', 'shared_statement', 'combined']
        source = next((s for role in roles for s in t['sources'] if s['role'] == role), t['sources'][0])
        return f"[{task_id}](../{source['path']}#page={source['page']})"

    text = f'''# Рабочая последовательность занятий с октября

{read('program.json')['author']}. 2026/2027 учебный год. Обновлено {display(plan['updated_on'])}.

Первое регулярное занятие - {display(plan['first_regular_session'])}. Вступительная олимпиада и её разбор уже прошли, но их даты и длительность не известны. Они не отмечены как проведённые пары нашей программы. Регулярных занятий, подтверждённых как проведённые, сейчас: {len(plan['completed_regular_sessions'])}.

Сегодня: [сценарий преподавателя](sessions/2026-10-03/teacher.md), [листок задач PDF](sessions/2026-10-03/student.pdf), [листок Word](sessions/2026-10-03/student.docx).

Школьный этап математики в Москве для 10 класса подтверждён на 13 октября 2026 года, с доступом 09:00-21:00 и длительностью 120 минут. Регистрация начинается 5 октября. [Официальная страница математики](https://vos.olimpiada.ru/subject/math). Следующая очная пара 17 октября будет уже после школьного этапа, поэтому перед ним есть только сегодняшнее занятие и самостоятельная работа. Точные сроки муниципального, регионального, заключительного этапов и МОШ нового сезона в проверенных официальных данных пока не подтверждены.

## Сколько занятий действительно помещается

По [графику лицея 1511]({plan['school_calendar_source']}) и [подписанному учебному графику]({plan['school_calendar_pdf_source']}) 10 класс завершает учебный год {display(plan['school_year_ends_on'])}. Последняя обычная суббота - {display(plan['last_regular_saturday'])}. Между сегодняшним занятием и этой датой {len(saturdays)} суббот, из них {len(blocked)} приходятся на каникулы. Если кружок в каникулы не проводится, остаётся {len(available)} возможных пар.

Преподаватель ожидает примерно {plan['mathematical_battle_saturdays_estimate']} субботних матбоёв; их точные даты пока неизвестны. При пяти отдельных отменах из-за матбоёв остаётся около {capacity} пар по 90 минут, то есть {capacity * 2} академических часов. Прочие отмены уменьшают этот объём. Если матбой совпадает с каникулами, дважды исключать субботу не нужно. Майские субботы пока оставлены резервными: проведение кружка нужно уточнить.

Кружки во время каникул допускаются общим графиком лицея, но для нашей группы такие встречи пока не подтверждены. Их отсутствие в таблице - рабочее предположение, а не утверждение о запрете. На 10 октября регулярную пару не рассчитываем; ближайшая предлагаемая дата после сегодня - 17 октября.

## Связь с годовой программой

[Программа из 34 тем](plan.md) и документ для сдачи сохраняют ранее заданный плановый объём 68 академических часов. Это исходная годовая программа, а не журнал проведённых занятий. Рабочая последовательность ниже выбирает из неё {len(core)} основных пар и {len(slots) - len(core)} дополнительных тем в резерве. Номера тем, цели, официальные задачи и домашняя работа берутся из тех же data/lessons.json и data/tasks.json. Тема 3 программы сегодня является фактическим занятием 1.

Соответствие тем и задач сохранено, но календарная вместимость меньше годового объёма. Сейчас нет подтверждённого расписания, которое позволяет провести все 34 пары. Домашняя работа и прошедшая вступительная олимпиада автоматически не заменяют недостающие пары. Если понадобится изменить плановый объём документа для сдачи, нужно согласованно изменить общую программу и её печатные версии; эта рабочая справка сама по себе их часы не меняет.

## Как читать даты и переносить темы

Все даты ниже, кроме сегодняшней готовой пары, - предложения при отсутствии матбоёв и прочих отмен. "Основа" означает тему, которую стараемся сохранить; "тур" - тренировку или её разбор; "резерв" - запасную субботу. Если на резервную дату не приходится перенос, можно провести указанную дополнительную тему. Это не обещание, что матбои выпадут именно на резервные даты.

При отмене пары исключаем её дату и переносим ещё не проведённую тему на следующую доступную субботу. В первую очередь занимаем резервные окна. Если отмен больше резерва, убираем углубление и сокращаем число классных задач, но не называем две непроведённые темы одной завершённой парой. Для основной тематической пары выбираем одну главную задачу и одну короткую вводную; оставшаяся задача допускается на дом.

После публикации дат олимпиад учебный муниципальный тур ставим за 1-2 доступные пары до муниципального этапа; два региональных тура и их разбор - за 2-3 пары до регионального; тур МОШ и его разбор - за 1-2 пары до МОШ. Эти вехи имеют приоритет над дополнительными темами. Если регион назначат раньше предложенных январских дат, переносим пробы в декабрь, используя резерв и вытесняя дополнительные темы. Резерв после олимпиады не компенсирует пропущенную подготовку перед ней.

До муниципального сохраняем чётность, остатки, углы, оценку и конструкцию, делимость и пробный тур. До регионального добавляем графы, двойной подсчёт, геометрические построения и два пробных дня с разбором. До МОШ ставим графовые конструкции, теорию чисел, геометрию и пробный тур с разбором. Эти группы тем записаны как ограничения в data/operational-plan.json: после внесения подтверждённой даты в календарь сборка остановится, если нужная подготовка назначена на день олимпиады или позже.

Для учеников, прошедших на заключительный этап, после регионального создаём индивидуальную подборку более трудных задач из тем 27, 28, 30, 31 и 32 и ставим её до опубликованной даты финала. Общий календарь группы сейчас ориентирован на муниципальный, региональный и МОШ; участие в финале ещё не известно. Дата заключительного этапа 2027 года не подтверждена, а его официальных комплектов в текущем банке нет.

## Предлагаемые субботы

В столбце "Тема программы" указан номер из исходных 34 тем, а не фактический порядковый номер проведённой пары. В PDF по ссылкам находятся оригинальные условия; отдельные сборники также содержат решения.

| Дата | Тема программы | Назначение | Задачи в классе |
| --- | --- | --- | --- |
'''
    labels = {'core': 'Основа', 'milestone': 'Тур или разбор', 'buffer': 'Резерв'}
    for slot in slots:
        lesson = lessons[slot['module']]
        title = f"{lesson['number']}. {lesson['title']}"
        if slot['date'] in prepared_sessions:
            session = prepared_sessions[slot['date']]
            directory = Path(slot['session_file']).parent.relative_to('course').as_posix()
            title = session['title'] + ' (части тем ' + ', '.join(map(str, session['programme_modules'])) + ')'
            material = f"[{len(session['tasks'])} задач на отдельном листке]({directory}/student.pdf); [решения и сценарий]({directory}/teacher.md)"
        else:
            material = '; '.join(problem(t) for t in lesson['classroom'])
        text += f"| {display(slot['date'])} | {title} | {labels[slot['priority']]} | {material} |\n"
    text += '\nКаникулы, исключённые из этой таблицы: ' + ', '.join(display(str(d)) for d in blocked) + '.\n\n'
    text += '''## Что рассказывать на ближайших парах

Сегодня подготовлены 10 задач из годовой программы. Первые пять: амёбы, числа из нулей и семёрок, табло, остатки трёх нечётных чисел и последняя цифра. Здесь чётность и инварианты переходят в остатки и десятичную запись. Следующие пять продолжают работу по делимости, раскраскам и конструкциям. Полные решения, подсказки и сценарий на 90 минут находятся в папке сегодняшнего занятия.

Отдельные задачи из тем 2, 3, 6 и 20 не означают четыре проведённые пары. На 17 октября сначала проверяем сегодняшнее продвижение: задачи 2, 4 и 5 с листка не выдаём снова как новые, если они уверенно разобраны. Тогда используем разбор школьного этапа и углубление метода остатков; темы делимости и раскрасок пока не считаем завершёнными.

'''
    for number in [2, 4, 5, 6, 11]:
        lesson = lessons[number]
        text += f"### {lesson['title']}\n\n{lesson['goal']} {lesson['notes']}\n\n"
        text += 'В классе: ' + '; '.join(problem(t) for t in lesson['classroom']) + '.\n\n'
        if lesson['homework']:
            text += 'Домашняя подборка: ' + '; '.join(problem(t) for t in lesson['homework']) + '.\n\n'
        text += '[Опорные решения и комментарии преподавателю](teacher.md).\n\n'
    text += '''## Что делать с остальными темами

Повторную диагностику не ставим: группа уже писала вступительную олимпиаду, а сегодняшняя письменная работа проверит качество доказательства. Игры, крайний элемент, показатели простых делителей, симметрия и многочлены остаются дополнительными темами в резервных окнах. Бесконечный спуск, стратегии вопросов, сложные геометрические неравенства и смешанные задачи можно выбирать после основных этапов при наличии времени. Все их официальные подборки остаются в годовой программе, даже если в фактический календарь они не помещаются.

При ограниченном времени до МОШ сначала сохранить тренировочный тур и разбор, затем теорию чисел и геометрию. Графовые конструкции уже поставлены перед пробным туром. Сокращённые туры в рамках пары не заменяют тренировку выносливости на настоящих 235 или 300 минутах; длинная самостоятельная проба остаётся дополнительной работой.

## Как фиксировать фактическую работу

После каждой пары записывать дату, тему, задачи, решённые самостоятельно и с подсказкой, и домашнюю работу. Предлагаемая дата сама по себе не означает проведённого занятия. Для изменения календаря используется data/operational-plan.json; таблица пересобирается командой python scripts/build_operational_plan.py. Подтверждённые даты матбоёв вносятся в mathematical_battle_dates, прочие отмены - в other_cancelled_dates; отменённая дата исключается из slots, а темы переносятся в оставшиеся окна. Матбой, совпавший с каникулами, не вычитает ещё одну доступную субботу. Темы и задачи изменяются через общую годовую программу, а не отдельно в этой справке.

Текущие сведения о датах этапов и источниках: [календарь олимпиад](../research/calendar.md). Точные даты матбоёв и дополнительные отмены ещё требуется внести по мере появления расписания.
'''
    (ROOT / 'course/operational-plan.md').write_text(text)
    print(f'Operational calendar: {len(available)} candidate Saturdays, {len(core)} core sessions, '
          f'{len(blocked)} holiday Saturdays')


if __name__ == '__main__':
    main()
