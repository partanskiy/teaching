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
    parser.add_argument('--submission-only',action='store_true',help='Rebuild only the submission files, preserving the detailed working plan')
    args=parser.parse_args()
    subprocess.run([sys.executable,str(ROOT/'scripts/build_submission.py')],cwd=ROOT,check=True)
    formal=ROOT/'course/План_для_сдачи_2026-2027.docx'
    working=ROOT/'course/План_34_занятия_2026-2027.docx'
    if not args.submission_only:
        subprocess.run(['pandoc',str(ROOT/'course/print-plan.md'),'--from=markdown','--to=docx',
                        '--reference-doc='+str(formal),'--output='+str(working)],cwd=ROOT,check=True)
    documents=[formal]if args.submission_only else [formal,working]
    if not args.skip_pdf:
        profile=Path(tempfile.mkdtemp(prefix='olympiad-math-export-'))
        try:
            subprocess.run(['libreoffice','--headless','--nologo','--nodefault','--nofirststartwizard',
                            '-env:UserInstallation='+profile.as_uri(),'--convert-to','pdf',
                            '--outdir',str(ROOT/'course'),*[str(path)for path in documents]],check=True)
            for path in [path.with_suffix('.pdf')for path in documents]:
                if not path.is_file():raise RuntimeError('PDF was not created: '+str(path))
        finally:
            shutil.rmtree(profile)
    subprocess.run([sys.executable,str(ROOT/'scripts/check_plans.py'),*(['--without-pdf']if args.skip_pdf else [])],cwd=ROOT,check=True)


if __name__=='__main__':main()
