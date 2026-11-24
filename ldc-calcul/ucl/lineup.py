import json,sys
for f in sys.argv[1:]:
    j=json.loads(json.loads(open(f).read())['rawHtml'])
    for r in j.get('rosters',[]):
        st=[p['athlete']['displayName'] for p in r.get('roster',[]) if p.get('starter')]
        print(r['team']['displayName'],len(st),':',', '.join(st))
