#!/usr/bin/env python3
"""Collect public source documents with the installed Python and lxml."""
import argparse
import concurrent.futures
import hashlib
import fcntl
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote, urlsplit, urlunsplit, quote
from urllib.request import Request, urlopen

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
PAGE_INDEX = ROOT / 'data/pages.json'


def read_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


def fetch(url, force=False):
    pages = read_json(PAGE_INDEX, {})
    if url in pages and not force:
        item = pages[url]
        if item.get('status') == 'ok' and (ROOT / item['path']).exists():
            return item
    key = hashlib.sha256(url.encode()).hexdigest()[:18]
    try:
        parts = urlsplit(url)
        request_url = urlunsplit((parts.scheme, parts.netloc.encode('idna').decode(),
                                 quote(parts.path, safe='/%:@!$&\'()*+,;=-._~'),
                                 quote(parts.query, safe='=&%:/?+@!$\'()*+,;~-._'), parts.fragment))
        # This public archive serves these exact files over HTTP. Its HTTPS
        # certificate does not cover the tasks subdomain; do not bypass TLS checks.
        if parts.hostname == 'tasks.olimpiada.ru':
            request_url = 'http://' + request_url.split('://', 1)[1]
        request = Request(request_url, headers={'User-Agent': 'Mozilla/5.0 (Educational archive, local research)'})
        with urlopen(request, timeout=30) as response:
            content = response.read(35 * 1024 * 1024 + 1)
            if len(content) > 35 * 1024 * 1024:
                raise ValueError('Document exceeds the 35 MiB collection limit')
            content_type = response.headers.get('Content-Type', '')
            final_url = response.url
        suffix = '.pdf' if content.startswith(b'%PDF') else '.html'
        if content.startswith(b'PK'):
            suffix = '.zip'
        if content.startswith(b'7z\xbc\xaf\x27\x1c'):
            suffix = '.7z'
        path = ROOT / 'sources/pages' / (key + suffix)
        path.write_bytes(content)
        item = {'url': url, 'final_url': final_url, 'status': 'ok',
                'download_url': request_url,
                'path': str(path.relative_to(ROOT)), 'content_type': content_type,
                'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content),
                'retrieved_at': datetime.now(timezone.utc).isoformat()}
    except Exception as exc:
        item = {'url': url, 'status': 'error', 'error': f'{type(exc).__name__}: {exc}',
                'retrieved_at': datetime.now(timezone.utc).isoformat()}
    return item


def links(item):
    if item.get('status') != 'ok' or not item['path'].endswith('.html'):
        return []
    content = (ROOT / item['path']).read_bytes()
    tree = parse_html(content)
    out = []
    for a in tree.xpath('//a[@href]'):
        href = urljoin(item.get('final_url', item['url']), a.get('href'))
        if not href.startswith(('https://', 'http://')):
            continue
        parent = a.getparent()
        for _ in range(2):
            if parent.getparent() is not None:
                parent = parent.getparent()
        out.append({'url': href, 'text': ' '.join(a.text_content().split()),
                    'context': ' '.join(parent.text_content().split())[:2500]})
    return out


def parse_html(content):
    encoding = re.search(br'charset\s*=\s*["\']?\s*([a-zA-Z0-9_-]+)', content[:20000], re.I)
    if encoding:
        codec = encoding.group(1).decode('ascii')
        try:
            return html.fromstring(content.decode(codec, errors='replace'))
        except LookupError:
            pass
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = content.decode('cp1251', errors='replace')
    return html.fromstring(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('urls', nargs='*')
    parser.add_argument('--url-file', type=Path)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--show-links', action='store_true')
    args = parser.parse_args()
    lock = (ROOT / 'data/collect.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX)
    urls = args.urls
    if args.url_file:
        urls.extend(line.strip() for line in args.url_file.read_text().splitlines()
                    if line.strip() and not line.startswith('#'))
    pages = read_json(PAGE_INDEX, {})
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(fetch, url, args.force): url for url in dict.fromkeys(urls)}
        for job in concurrent.futures.as_completed(jobs):
            item = job.result()
            pages[item['url']] = item
            print(item['status'], item['url'], item.get('bytes', item.get('error', '')), flush=True)
            write_json(PAGE_INDEX, pages)
    if args.show_links:
        for url in urls:
            print(json.dumps({'source': url, 'links': links(pages[url])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
