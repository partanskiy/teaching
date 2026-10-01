#!/usr/bin/env python3
"""Verify checked-out LFS originals and extract text; optionally restore a Release."""
import argparse
import concurrent.futures
import hashlib
import json
import zipfile
from pathlib import Path,PurePosixPath
from urllib.request import Request,urlopen
from build_archive import extract
from collect import ROOT,write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',action='store_true',help='Restore the pinned Release archive instead of using Git LFS files')
    parser.add_argument('--from-file',type=Path);parser.add_argument('--replace',action='store_true')
    args=parser.parse_args()
    docs=json.loads((ROOT/'data/documents.json').read_text())
    if not args.release and args.from_file is None:
        if args.replace:parser.error('--replace requires --release or --from-file')
        for document in docs:
            path=ROOT/document['path']
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=document['sha256'] or path.stat().st_size!=document['bytes']:
                raise ValueError('Missing or changed original: '+document['path']+'. Run git lfs pull, or explicitly use --release for the published snapshot.')
        with concurrent.futures.ThreadPoolExecutor(max_workers=6)as pool:
            docs=list(pool.map(extract,docs))
        write_json(ROOT/'data/documents.json',docs)
        print(f'Verified {len(docs)} checked-out originals and prepared the text index; no network downloads.')
        return
    release=json.loads((ROOT/'data/release.json').read_text());asset=release['materials']
    path=args.from_file
    if path is None:
        target=ROOT/'dist';target.mkdir(exist_ok=True);path=target/asset['asset']
        if not path.is_file()or hashlib.sha256(path.read_bytes()).hexdigest()!=asset['sha256']:
            request=Request(asset['url'],headers={'User-Agent':'olympiad-math educational archive'})
            with urlopen(request,timeout=60)as response:path.write_bytes(response.read())
    if hashlib.sha256(path.read_bytes()).hexdigest()!=asset['sha256']:raise ValueError('Release archive checksum differs')
    expected={d['path']:d for d in docs}
    count=0
    with zipfile.ZipFile(path)as z:
        if set(z.namelist())!=set(expected):raise ValueError('Release archive and document manifest differ')
        for member in z.infolist():
            pure=PurePosixPath(member.filename)
            if pure.is_absolute()or '..'in pure.parts:raise ValueError('Unsafe archive path')
            destination=ROOT/member.filename
            if not destination.resolve().is_relative_to(ROOT.resolve()):raise ValueError('Archive path outside project')
            checksum=expected[member.filename]['sha256']
            if destination.is_file():
                if hashlib.sha256(destination.read_bytes()).hexdigest()==checksum:continue
                if not args.replace:raise FileExistsError('Local file differs: '+member.filename)
            content=z.read(member)
            if hashlib.sha256(content).hexdigest()!=checksum:raise ValueError('Document checksum differs: '+member.filename)
            destination.parent.mkdir(parents=True,exist_ok=True)
            temporary=destination.with_name(destination.name+'.restore-tmp');temporary.write_bytes(content);temporary.replace(destination);count+=1
    with concurrent.futures.ThreadPoolExecutor(max_workers=6)as pool:
        docs=list(pool.map(extract,docs))
    write_json(ROOT/'data/documents.json',docs)
    print(f'Restored {count} documents; verified {len(docs)} original files from release '+release['tag'])


if __name__=='__main__':main()
