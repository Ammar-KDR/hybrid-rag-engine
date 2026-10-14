#!/usr/bin/env python3
"""Download official Jordanian government service files (run while ONLINE).

No non-stdlib Python packages are needed. Files are checked for PDF magic bytes.
The script NEVER downloads evaluation answer keys into the ingestion directory.
"""
import json, pathlib, urllib.request, urllib.error, time, sys
HERE=pathlib.Path(__file__).resolve().parent
DEST=HERE/'downloaded_official_docs'
DEST.mkdir(parents=True,exist_ok=True)
sources=json.loads((HERE/'sources.json').read_text(encoding='utf-8'))
failed=[]
for row in sources:
    url=row['url']; dest=DEST/row['local_filename']
    if dest.exists() and dest.stat().st_size>300:
        print('SKIP',row['source_id'],dest)
        continue
    ok=False
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; EducationalRAGTest/1.0)','Accept':'application/pdf,text/html,*/*'})
            with urllib.request.urlopen(req,timeout=25) as res:
                payload=res.read(25*1024*1024+1)
                ct=res.headers.get('content-type','')
            if len(payload)>25*1024*1024:raise RuntimeError('file over 25 MB; download manually')
            if row['format']=='pdf' and not payload.startswith(b'%PDF-'):
                raise RuntimeError(f'not a PDF (content type: {ct})')
            if row['format']=='html' and b'html' not in payload[:3000].lower():
                raise RuntimeError(f'not HTML (content type: {ct})')
            if len(payload)<300:raise RuntimeError('unexpectedly small file')
            dest.write_bytes(payload)
            print('OK',row['source_id'],len(payload),'bytes',dest)
            ok=True;break
        except Exception as exc:
            print('RETRY',row['source_id'],attempt+1,type(exc).__name__,str(exc)[:150])
            time.sleep(1.5*(attempt+1))
    if not ok:failed.append(row)
print(f'Completed: {len(sources)-len(failed)}/{len(sources)} downloads. Destination: {DEST}')
if failed:
    print('Download manually from the official links:')
    for row in failed:print(row['source_id'],row['url'])
    sys.exit(1)
