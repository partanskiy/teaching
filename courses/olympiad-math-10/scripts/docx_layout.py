from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E


NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}
W = NS['w']
R = NS['r']
RELS = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'


def el(tag, parent=None, **attrs):
    node = E.Element(f'{{{W}}}{tag}')
    for key, value in attrs.items():
        node.set(f'{{{W}}}{key}', str(value))
    if parent is not None:
        parent.append(node)
    return node


def xml(node):
    return E.tostring(node, encoding='UTF-8', xml_declaration=True, standalone=True)


document = E.Element(f'{{{W}}}document', nsmap=NS)
body = el('body', document)
hyperlinks = []


def run(parent, text, bold=False, size=None, underline=False):
    r = el('r', parent)
    rp = el('rPr', r)
    if bold:
        el('b', rp)
    if size:
        el('sz', rp, val=round(size * 2))
        el('szCs', rp, val=round(size * 2))
    if underline:
        el('u', rp, val='single')
    t = el('t', r)
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t.text = text
    return r


def paragraph(text='', style='Normal', align=None, bold=False, size=None,
              before=None, after=None, indent=None, left=None, line=None, parent=None,
              keep=False):
    parent = body if parent is None else parent
    p = el('p', parent)
    pp = el('pPr', p)
    el('pStyle', pp, val=style)
    if keep:
        el('keepNext', pp)
    el('widowControl', pp)
    if any(x is not None for x in (before, after, line)):
        args = {}
        if before is not None:
            args['before'] = before
        if after is not None:
            args['after'] = after
        if line is not None:
            args.update(line=line, lineRule='auto')
        el('spacing', pp, **args)
    if indent is not None or left is not None:
        ind = {}
        if indent is not None:
            ind['firstLine'] = indent
        if left is not None:
            ind['left'] = left
        el('ind', pp, **ind)
    if align:
        el('jc', pp, val=align)
    if text:
        run(p, text, bold=bold, size=size)
    return p


def heading(text):
    return paragraph(text, 'Heading1')


def subheading(text):
    return paragraph(text, 'Heading2')


def item(text):
    return paragraph(text, 'ListText')


def pagebreak():
    p = el('p', body)
    pp = el('pPr', p)
    el('spacing', pp, before=0, after=0, line=20, lineRule='exact')
    rp = el('rPr', pp)
    el('sz', rp, val=2)
    r = el('r', p)
    el('br', r, type='page')


def table(rows, widths, size=11, header=True, total=False, shaded=True):
    t = el('tbl', body)
    props = el('tblPr', t)
    el('tblW', props, w=sum(widths), type='dxa')
    el('tblLayout', props, type='fixed')
    borders = el('tblBorders', props)
    for name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        el(name, borders, val='single', sz=4, color='777777')
    margins = el('tblCellMar', props)
    for name, width in [('top', 60), ('left', 90), ('bottom', 60), ('right', 90)]:
        el(name, margins, w=width, type='dxa')
    grid = el('tblGrid', t)
    for width in widths:
        el('gridCol', grid, w=width)
    for ri, row in enumerate(rows):
        tr = el('tr', t)
        trp = el('trPr', tr)
        el('cantSplit', trp)
        if ri == 0 and header:
            el('tblHeader', trp)
        is_bold = (header and ri == 0) or (total and ri == len(rows) - 1)
        for ci, (value, width) in enumerate(zip(row, widths)):
            cell = el('tc', tr)
            cp = el('tcPr', cell)
            el('tcW', cp, w=width, type='dxa')
            el('vAlign', cp, val='center')
            if is_bold and shaded:
                el('shd', cp, fill='EFEFEF', val='clear')
            numeric = str(value).isdigit() or (header and ri == 0)
            paragraph(str(value), style='TableText', align='center' if numeric else 'left',
                      size=size, bold=is_bold, after=0, indent=0, line=240, parent=cell)
    paragraph('', style='TableText', after=30, line=120)
    return t


def reference(number, description, url=None):
    p = paragraph(f'{number}. {description}', style='Reference')
    if url:
        run(p, ' ')
        link = el('hyperlink', p)
        rid = f'rIdLink{len(hyperlinks) + 1}'
        link.set(f'{{{R}}}id', rid)
        run(link, url, underline=True, size=11)
        hyperlinks.append((rid, url))
    return p



def save(out, *, title, author, lessons, sections, page_numbers=True):
    sect = el('sectPr', body)
    if page_numbers:
        footer_ref = el('footerReference', sect, type='default')
        footer_ref.set(f'{{{R}}}id', 'rIdFooter')
    el('pgSz', sect, w=11906, h=16838)
    el('pgMar', sect, top=1134, right=850, bottom=1134, left=1701, header=708, footer=708, gutter=0)
    el('titlePg', sect)


    styles = E.Element(f'{{{W}}}styles', nsmap={'w': W})
    defaults = el('docDefaults', styles)
    rdef = el('rPrDefault', defaults)
    rp = el('rPr', rdef)
    el('rFonts', rp, ascii='Times New Roman', hAnsi='Times New Roman', eastAsia='Times New Roman', cs='Times New Roman')
    el('sz', rp, val=24)
    el('szCs', rp, val=24)
    el('lang', rp, val='ru-RU')
    pdef = el('pPrDefault', defaults)
    pp = el('pPr', pdef)
    el('spacing', pp, after=80, line=360, lineRule='auto')


    def style(sid, name, *, align='both', indent=570, line=360, after=80,
              before=0, bold=False, size=12, keep=False, outline=None):
        st = el('style', styles, type='paragraph', styleId=sid)
        if sid == 'Normal':
            st.set(f'{{{W}}}default', '1')
        el('name', st, val=name)
        if sid != 'Normal':
            el('basedOn', st, val='Normal')
        el('next', st, val='Normal')
        el('qFormat', st)
        pp = el('pPr', st)
        if keep:
            el('keepNext', pp)
        el('widowControl', pp)
        el('spacing', pp, before=before, after=after, line=line, lineRule='auto')
        el('ind', pp, firstLine=indent)
        el('jc', pp, val=align)
        if outline is not None:
            el('outlineLvl', pp, val=outline)
        rp = el('rPr', st)
        if bold:
            el('b', rp)
        el('sz', rp, val=round(size * 2))
        el('szCs', rp, val=round(size * 2))


    style('Normal', 'Normal')
    style('Cover', 'Cover', align='center', indent=0, line=276, after=80)
    style('Heading1', 'heading 1', align='center', indent=0, line=276, before=120, after=200, bold=True, size=12, keep=True, outline=0)
    style('Heading2', 'heading 2', align='left', indent=0, line=276, before=120, after=80, bold=True, keep=True, outline=1)
    style('ListText', 'List Text', align='both', indent=0, line=360, after=60)
    style('Caption', 'Caption', align='left', indent=0, line=276, after=120)
    style('TableText', 'Table Text', align='left', indent=0, line=240, after=0, size=11)
    style('Reference', 'Reference', align='left', indent=0, line=276, after=100, size=11)


    footer = E.Element(f'{{{W}}}ftr', nsmap={'w': W})
    p = el('p', footer)
    pp = el('pPr', p)
    el('jc', pp, val='center')
    rp = el('rPr', pp)
    el('sz', rp, val=20)
    r = el('r', p)
    el('fldChar', r, fldCharType='begin')
    r = el('r', p)
    el('instrText', r).text = ' PAGE '
    r = el('r', p)
    el('fldChar', r, fldCharType='separate')
    run(p, '1', size=10)
    r = el('r', p)
    el('fldChar', r, fldCharType='end')

    settings = E.Element(f'{{{W}}}settings', nsmap={'w': W})
    el('zoom', settings, percent=100)
    el('defaultTabStop', settings, val=709)
    el('updateFields', settings, val='true')
    compat = el('compat', settings)
    el('compatSetting', compat, name='compatibilityMode', uri='http://schemas.microsoft.com/office/word', val=15)


    docrels = E.Element(f'{{{RELS}}}Relationships', nsmap={None: RELS})
    for rid, kind, target in [('rIdStyles', 'styles', 'styles.xml'),
                              ('rIdSettings', 'settings', 'settings.xml'),
                              ('rIdFooter', 'footer', 'footer1.xml')]:
        E.SubElement(docrels, f'{{{RELS}}}Relationship', Id=rid,
                     Type=f'{R}/{kind}', Target=target)
    for rid, url in hyperlinks:
        E.SubElement(docrels, f'{{{RELS}}}Relationship', Id=rid,
                     Type=f'{R}/hyperlink', Target=url, TargetMode='External')

    core_ns = {
        'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'dcterms': 'http://purl.org/dc/terms/',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    }
    core = E.Element(f'{{{core_ns["cp"]}}}coreProperties', nsmap=core_ns)
    for name, value in [('title', title),
                        ('subject', 'Дополнительная общеобразовательная общеразвивающая программа'),
                        ('creator', author),
                        ('description', '34 занятия по субботам, 90 минут; 68 академических часов.')]:
        E.SubElement(core, f'{{{core_ns["dc"]}}}{name}').text = value
    E.SubElement(core, f'{{{core_ns["cp"]}}}lastModifiedBy').text = author
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    for name in ['created', 'modified']:
        node = E.SubElement(core, f'{{{core_ns["dcterms"]}}}{name}')
        node.set(f'{{{core_ns["xsi"]}}}type', 'dcterms:W3CDTF')
        node.text = now

    app_ns = 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'
    app = E.Element(f'{{{app_ns}}}Properties', nsmap={None: app_ns})
    E.SubElement(app, f'{{{app_ns}}}Application').text = 'Microsoft Office Word'

    rootrels = E.Element(f'{{{RELS}}}Relationships', nsmap={None: RELS})
    for rid, typ, target in [
        ('rId1', f'{R}/officeDocument', 'word/document.xml'),
        ('rId2', 'http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties', 'docProps/core.xml'),
        ('rId3', f'{R}/extended-properties', 'docProps/app.xml'),
    ]:
        E.SubElement(rootrels, f'{{{RELS}}}Relationship', Id=rid, Type=typ, Target=target)

    types = E.Element(f'{{{CT}}}Types', nsmap={None: CT})
    E.SubElement(types, f'{{{CT}}}Default', Extension='rels', ContentType='application/vnd.openxmlformats-package.relationships+xml')
    E.SubElement(types, f'{{{CT}}}Default', Extension='xml', ContentType='application/xml')
    for name, content_type in [
        ('word/document.xml', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'),
        ('word/styles.xml', 'application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml'),
        ('word/settings.xml', 'application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml'),
        ('word/footer1.xml', 'application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml'),
        ('docProps/core.xml', 'application/vnd.openxmlformats-package.core-properties+xml'),
        ('docProps/app.xml', 'application/vnd.openxmlformats-officedocument.extended-properties+xml'),
    ]:
        E.SubElement(types, f'{{{CT}}}Override', PartName=f'/{name}', ContentType=content_type)

    payloads = {
        '[Content_Types].xml': types,
        '_rels/.rels': rootrels,
        'word/document.xml': document,
        'word/_rels/document.xml.rels': docrels,
        'word/styles.xml': styles,
        'word/settings.xml': settings,
        'word/footer1.xml': footer,
        'docProps/core.xml': core,
        'docProps/app.xml': app,
    }
    all_text = ''.join(document.xpath('//w:t/text()', namespaces=NS))
    for character in '\u00ab\u00bb\u201c\u201d\u2018\u2019\u2013\u2014\u2026\u2192\u00a0':
        assert character not in all_text, f'Unexpected typography: {character!r}'
    assert 'Червяков' not in all_text

    with ZipFile(out, 'w', ZIP_DEFLATED) as z:
        for name, node in payloads.items():
            z.writestr(name, xml(node))
    print(out)
    print('Lessons:', len(lessons), 'Academic hours:', sum(n * 2 for _, n in sections))
    print('Words:', len(all_text.split()), 'Characters:', len(all_text))
