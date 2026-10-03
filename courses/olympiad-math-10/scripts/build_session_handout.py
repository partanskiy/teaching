#!/usr/bin/env python3
"""Render a dated student handout using system Pandoc and LibreOffice."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session', help='Session directory name, for example 2026-10-03')
    args = parser.parse_args()
    session = ROOT / 'course/sessions' / args.session
    source = session / 'student.md'
    if not source.is_file():
        parser.error('Student handout does not exist: ' + str(source))
    program = json.loads((ROOT / 'data/program.json').read_text())
    output = session / 'student.docx'
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
