#!/usr/bin/env python3
"""Package binary Release assets without putting them into Git history."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(path,files):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for file in sorted(files):
            name=str(file.relative_to(ROOT))
            info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            z.writestr(info,file.read_bytes())


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--tag',required=True)
    args=parser.parse_args();DIST.mkdir(exist_ok=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/check_plans.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/validate.py')],check=True)
    docs=json.loads((ROOT/'data/documents.json').read_text())
    materials=DIST/'olympiad-math-materials.zip'
    archive(materials,[ROOT/d['path']for d in docs])
    files={
        'submission-plan.docx':'course/План_для_сдачи_2026-2027.docx',
        'submission-plan.pdf':'course/План_для_сдачи_2026-2027.pdf',
        'working-plan.docx':'course/План_34_занятия_2026-2027.docx',
        'working-plan.pdf':'course/План_34_занятия_2026-2027.pdf'
    }
    for name,source in files.items():shutil.copyfile(ROOT/source,DIST/name)
    base='https://github.com/partanskiy/olympiad-math/releases/download/'+args.tag+'/'
    release={'repository':'partanskiy/olympiad-math','tag':args.tag,
             'materials':{'asset':materials.name,'url':base+materials.name,'sha256':digest(materials),'bytes':materials.stat().st_size},
             'plans':{name:{'url':base+name,'sha256':digest(DIST/name)}for name in files}}
    (ROOT/'data/release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n')
    selected=[]
    for directory in ['archive','data','course','research','scripts','site','.github','extracted/full']:
        for file in (ROOT/directory).rglob('*'):
            if file.is_file() and '__pycache__'not in file.parts and file.suffix not in ['.log','.pyc'] and file.name!='collect.lock':selected.append(file)
    selected.extend(ROOT/name for name in ['README.md','index.html','BINARY_FLOW.md','NOTICE.md','AGENTS.md','.gitignore','.gitattributes'] if (ROOT/name).is_file())
    offline=DIST/'olympiad-math-offline.zip';archive(offline,selected)
    assets=[materials,offline,*[DIST/name for name in files]]
    (DIST/'SHA256SUMS.txt').write_text(''.join(digest(p)+'  '+p.name+'\n'for p in assets))
    stats=json.loads((ROOT/'data/statistics.json').read_text())
    (DIST/'release-notes.md').write_text(f'''Олимпиадная математика 10 класса, 2026/2027. Партанский Илья Михайлович.

Два согласованных плана на 34 субботних занятия по 90 минут: программа для сдачи в формате исходного документа и рабочий план с конкретными задачами. Темы, порядок занятий, цели и часы строятся из общих данных.

Сохранено {stats['documents']} документов: региональный этап ВсОШ 2010-2026, МОШ 2011-2026, муниципальные комплекты из {stats['municipal_regions']} регионов. Все 250 задач основного ядра размечены после чтения; муниципальная разметка вне проверенной выборки предварительная.

Для готовой локальной работы распаковать olympiad-math-offline.zip и открыть index.html. Для Git-клона восстановить оригиналы командой python scripts/restore_materials.py. Архивные PDF и готовые документы хранятся во вложениях релиза, вне истории Git. SHA256SUMS.txt содержит суммы вложений.
''')
    print(json.dumps({p.name:round(p.stat().st_size/1024/1024,2)for p in assets},ensure_ascii=False))


if __name__=='__main__':main()
