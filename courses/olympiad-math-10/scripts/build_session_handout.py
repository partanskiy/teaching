#!/usr/bin/env python3
"""Render a dated Typst handout, with legacy Markdown/DOCX support."""
import argparse
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session', help='Session directory name, for example 2026-10-03')
    parser.add_argument('--variant', choices=['student', 'advanced'], default='student',
                        help='Main handout or an additional advanced selection')
    args = parser.parse_args()
    session = ROOT / 'course/sessions' / args.session
    source = session / (args.variant + '.md')
    typst_source = session / (args.variant + '.typ')
    if not source.is_file() and not typst_source.is_file():
        parser.error('Student handout does not exist: ' + str(source))
    program = json.loads((ROOT / 'data/program.json').read_text())
    manifest_path = session / ('session.json' if args.variant == 'student' else 'advanced.json')
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
    if manifest:
        tasks = {t['id']: t for t in json.loads((ROOT / 'data/tasks.json').read_text())}
        lessons = {l['number']: l for l in json.loads((ROOT / 'data/lessons.json').read_text())}
        selected = manifest['tasks']
        if len({item['id'] for item in selected}) != len(selected):
            raise ValueError('Session tasks must be distinct')
        if [item['number'] for item in selected] != list(range(1, len(selected) + 1)):
            raise ValueError('Session task numbers must be consecutive')
        for item in selected:
            task = tasks[item['id']]
            lesson = lessons[item['programme_module']]
            supplemental = args.variant == 'advanced' and manifest.get('kind') == 'supplemental'
            if supplemental and (
                task['grade'] != manifest['grade']
                or (task['competition'], task['stage']) not in [('vsosh', 'regional'), ('mosh', 'main')]
            ):
                raise ValueError('Advanced selection must use official regional or MOSH tasks of its grade')
            if task['reserve'] or (
                item['id'] not in lesson['classroom'] + lesson['homework'] and not supplemental
            ):
                raise ValueError('Session task must belong to the stated module and not be reserved')
    if typst_source.is_file():
        pdf = session / (args.variant + '.pdf')
        timestamp = []
        if manifest.get('date'):
            epoch = int(datetime.fromisoformat(manifest['date']).replace(tzinfo=timezone.utc).timestamp())
            timestamp = ['--creation-timestamp', str(epoch)]
        subprocess.run([
            'typst', 'compile', *timestamp, '--root', str(ROOT), str(typst_source), str(pdf),
        ], check=True)
        print(pdf)
        return
    output = session / (args.variant + '.docx')
    subprocess.run([
        'pandoc', str(source), '--from=markdown', '--to=docx',
        '--reference-doc=' + str(ROOT / 'course/План_для_сдачи_2026-2027.docx'),
        '--output=' + str(output),
    ], check=True)
    with ZipFile(output) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    styles = etree.fromstring(parts['word/styles.xml'])
    for style in styles.findall('w:style', NS):
        if style.get('{' + W + '}styleId') in ['Normal', 'BodyText', 'FirstParagraph']:
            properties = style.find('w:pPr', NS)
            if properties is None:
                properties = etree.SubElement(style, '{' + W + '}pPr')
            spacing = properties.find('w:spacing', NS)
            if spacing is None:
                spacing = etree.SubElement(properties, '{' + W + '}spacing')
            for key, value in [('line', '276'), ('lineRule', 'auto'), ('after', '90')]:
                spacing.set('{' + W + '}' + key, value)
            indent = properties.find('w:ind', NS)
            if indent is not None:
                indent.set('{' + W + '}firstLine', '0')
    document = etree.fromstring(parts['word/document.xml'])
    for paragraph in document.findall('.//w:body/w:p', NS):
        text = ''.join(paragraph.itertext())
        if any(text == 'Задача ' + str(n) for n in manifest.get('page_break_before', [])):
            properties = paragraph.find('w:pPr', NS)
            if properties is None:
                properties = etree.SubElement(paragraph, '{' + W + '}pPr')
            etree.SubElement(properties, '{' + W + '}pageBreakBefore')
    core = etree.fromstring(parts['docProps/core.xml'])
    dc = 'http://purl.org/dc/elements/1.1/'
    creator = core.find('{' + dc + '}creator')
    if creator is None:
        creator = etree.SubElement(core, '{' + dc + '}creator')
    creator.text = program['author']
    for margin in document.findall('.//w:pgMar', NS):
        for side in ['top', 'bottom', 'left', 'right']:
            margin.set('{' + W + '}' + side, '850')
    for name, tree in [('word/styles.xml', styles), ('word/document.xml', document),
                       ('docProps/core.xml', core)]:
        parts[name] = etree.tostring(tree, encoding='UTF-8', xml_declaration=True, standalone=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)
    with tempfile.TemporaryDirectory(prefix='teaching-handout-') as directory:
        subprocess.run([
            'libreoffice', '--headless', '--nologo', '--nodefault', '--nofirststartwizard',
            '-env:UserInstallation=' + Path(directory).as_uri(),
            '--convert-to', 'pdf', '--outdir', str(session), str(output),
        ], check=True)
    pdf = output.with_suffix('.pdf')
    if not pdf.is_file():
        raise RuntimeError('PDF was not created: ' + str(pdf))
    print(pdf)


if __name__ == '__main__':
    main()
