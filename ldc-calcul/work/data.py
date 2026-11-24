import glob, re, json, unicodedata, parse
KEYS=[('gazelec','Gazélec Ajaccio'),('ajaccio','AC Ajaccio'),('saint-germain','Paris Saint-Germain'),('paris fc','Paris FC'),
('auxerre','AJ Auxerre'),('monaco','AS Monaco'),('nancy','AS Nancy'),('etienne','AS Saint-Étienne'),('amiens','Amiens SC'),
('angers','Angers SCO'),('clermont','Clermont Foot'),('dijon','Dijon FCO'),('guingamp','EA Guingamp'),('troyes','ES Troyes AC'),
('lorient','FC Lorient'),('metz','FC Metz'),('nantes','FC Nantes'),('bordeaux','Girondins Bordeaux'),('havre','Le Havre AC'),
('le mans','Le Mans FC'),('lens','RC Lens'),('lille','LOSC Lille'),('montpellier','Montpellier HSC'),('nimes','Nîmes Olympique'),
('nice','OGC Nice'),('lyon','Olympique Lyonnais'),('marseille','Olympique de Marseille'),('strasbourg','RC Strasbourg'),
('rennes','Stade Rennais'),('rennais','Stade Rennais'),('bastia','SC Bastia'),('caen','SM Caen'),('brest','Stade Brestois'),
('reims','Stade de Reims'),('toulouse','Toulouse FC'),('evian','Évian TG')]
def canon(n):
    s=unicodedata.normalize('NFD',n).encode('ascii','ignore').decode().lower()
    for k,v in KEYS:
        if k in s: return v
    raise ValueError(n)
def seasons():
    """liste de (saison, [ (md,home,away,hg,ag) ])  — saisons passées + saison en cours (fichier du prédicteur)"""
    out=[]
    for f in sorted(glob.glob(parse.D+'/*_fr1.txt')):
        y=re.search(r'(\d{4}-\d{2})_fr1',f).group(1)
        if y=='2026-27': continue
        out.append((y,[(m,canon(h),canon(a),x,z) for m,h,a,x,z in parse.parse(f)]))
    out.append(('2026-27',current()))
    return out
def current():
    txt=open('/home/claude/coxewagen/predicteur-ligue1/index.html',encoding='utf-8').read()
    j=re.search(r'let MATCHDAY_HISTORY = (\{[\s\S]*?\});',txt).group(1)
    H=json.loads(j); r=[]
    for k in sorted(H,key=int):
        for g in H[k]:
            r.append((int(k),canon(g['home']),canon(g['away']),g.get('homeScore'),g.get('awayScore'),g.get('played',False)))
    return r
if __name__=='__main__':
    for y,m in seasons(): print(y,len(m),len({x[1] for x in m}))
    c=current(); print('played',sum(1 for x in c if x[5]),'total',len(c)); print([x for x in c if not x[5]][:12])
