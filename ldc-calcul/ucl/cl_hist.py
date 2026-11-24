import re, csv, json, glob, unicodedata, bisect, datetime as dt
MON={m:i+1 for i,m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}
rows=[]
for f in sorted(glob.glob('data/ofcl/*/cl.txt')):
    season=f.split('/')[-2]; y1=int(season[:4]); cur=None; stage=''
    for line in open(f,encoding='utf-8'):
        if line.startswith('▪'): stage=line.strip('▪ \n'); continue
        m=re.search(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\w{3}) (\d+)(?: (\d{4}))?',line)
        if m and ' v ' not in line:
            mo=MON[m.group(2)]; yr=int(m.group(4)) if m.group(4) else (y1 if mo>=7 else y1+1)
            cur=dt.date(yr,mo,int(m.group(3))); continue
        m=re.search(r'^\s*(?:\d\d:\d\d\s+)?(.+?) \((\w{3})\)\s+v\s+(.+?) \((\w{3})\)\s+(\d+)-(\d+)',line)
        if m and cur:
            rows.append(dict(season=season,date=str(cur),stage=stage,h=m.group(1).strip(),hc=m.group(2),a=m.group(3).strip(),ac=m.group(4),hg=int(m.group(5)),ag=int(m.group(6)),final='Final' in stage and 'Quarter' not in stage and 'Semi' not in stage))
print(len(rows)); json.dump(rows,open('cl_hist_raw.json','w'),ensure_ascii=False)
from collections import Counter; print(Counter(r['season'] for r in rows))
