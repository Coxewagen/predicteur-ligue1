import json,glob,csv,unicodedata,re
D='/tmp/claude-tool-results/7fb589f8-f543-5abb-af55-3c549d73a470/'
games={}; teams=set()
for f in glob.glob(D+'*.txt')+glob.glob(D+'*.json'):
    try:
        o=json.load(open(f)); raw=o[0]['text'] if isinstance(o,list) else None
        j=json.loads(json.loads(raw)['rawHtml']) if raw else json.loads(o['rawHtml'])
    except Exception: continue
    if 'team' not in j or 'events' not in j: continue
    teams.add(j['team']['displayName'])
    for e in j['events']:
        c=e['competitions'][0]
        st=(c.get('status') or e.get('status') or {}).get('type',{})
        if st.get('state')!='post': continue
        comp=e['seasonType']['name']
        if 'Friendly' in comp: continue
        if e['date'][:10]<'2026-09-02': continue
        h=[x for x in c['competitors'] if x['homeAway']=='home'][0]; a=[x for x in c['competitors'] if x['homeAway']=='away'][0]
        sc=lambda x:int(float(x['score']['value'] if isinstance(x['score'],dict) else x['score']))
        games[e['id']]=(e['date'][:16],comp,h['team']['displayName'],a['team']['displayName'],sc(h),sc(a),int(c.get('neutralSite',False)))
json.dump(sorted(games.values()),open('allgames.json','w'),ensure_ascii=False)
print(len(games),'matchs;',len(teams),'équipes:',sorted(teams))
