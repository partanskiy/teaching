#!/usr/bin/env python3
"""Build both synchronized plans and optionally render PDFs with LibreOffice."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-pdf',action='store_true')
    args=parser.parse_args()
    subprocess.run([sys.executable,str(ROOT/'scripts/build_submission.py')],cwd=ROOT,check=True)
    formal=ROOT/'course/План_для_сдачи_2026-2027.docx'
    working=ROOT/'course/План_34_занятия_2026-2027.docx'
    subprocess.run(['pandoc',str(ROOT/'course/print-plan.md'),'--from=markdown','--to=docx',
                    '--reference-doc='+str(formal),'--output='+str(working)],cwd=ROOT,check=True)
    if not args.skip_pdf:
        profile=Path(tempfile.mkdtemp(prefix='olympiad-math-export-'))
        try:
            subprocess.run(['libreoffice','--headless','--nologo','--nodefault','--nofirststartwizard',
                            '-env:UserInstallation='+profile.as_uri(),'--convert-to','pdf',
                            '--outdir',str(ROOT/'course'),str(formal),str(working)],check=True)
            for path in [formal.with_suffix('.pdf'),working.with_suffix('.pdf')]:
                if not path.is_file():raise RuntimeError('PDF was not created: '+str(path))
        finally:
            shutil.rmtree(profile)
    subprocess.run([sys.executable,str(ROOT/'scripts/check_plans.py'),*(['--without-pdf']if args.skip_pdf else [])],cwd=ROOT,check=True)


if __name__=='__main__':main()
