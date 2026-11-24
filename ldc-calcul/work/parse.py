import re, json, glob, os, sys
D='/home/claude/data/france/france'
FMT_A=re.compile(r'^\s*(?:\d{1,2}[:.]\d{2}\s+)?(.+?)\s+v\s+(.+?)\s+(\d+)-(\d+)(?:\s|$)')
FMT_B=re.compile(r'^\s*(?:\d{1,2}[:.]\d{2}\s+)?(.+?)\s+(\d+)-(\d+)(?:\s+\(\d+-\d+\))?\s+(.+?)\s*$')
MD=re.compile(r'(?:Matchday|Regular Season -|Journée|Round)\s*(\d+)',re.I)
def parse(path):
    out=[];md=None
    for line in open(path,encoding='utf-8'):
        if line.startswith('#') or line.startswith('='): continue
        m=MD.search(line)
        if '▪' in line or line.lstrip().startswith('»'):
            if m: md=int(m.group(1))
            continue
        s=line.rstrip()
        if not s.strip() or s.strip().startswith('('): continue
        if re.match(r'^\s*(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b',s) and not re.search(r'\d-\d',s[15:]): continue
        s2=re.sub(r'^\s*(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+\s+\d+(\s+\d{4})?','',s)
        a=FMT_A.match(s2)
        if a: out.append((md,a.group(1).strip(),a.group(2).strip(),int(a.group(3)),int(a.group(4))));continue
        b=FMT_B.match(s2)
        if b and not re.search(r"\d'",s2): out.append((md,b.group(1).strip(),b.group(4).strip(),int(b.group(2)),int(b.group(3))))
    return out
if __name__=='__main__':
    for f in sorted(glob.glob(D+'/*_fr[12].txt')):
        r=parse(f); teams=sorted({x[1] for x in r}|{x[2] for x in r})
        print(os.path.basename(f),len(r),len(teams))
