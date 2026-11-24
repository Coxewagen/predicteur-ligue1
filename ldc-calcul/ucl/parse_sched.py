import json,sys
o=json.load(open(sys.argv[1])); t=o[0]['text'] if isinstance(o,list) else None
j=json.loads(json.loads(t)['rawHtml']) if t else json.loads(json.load(open(sys.argv[1]))['rawHtml'])
for e in j['events']:
    c=e['competitions'][0]
    if not c.get('status',e.get('status',{})).get('type',{}).get('completed', False): 
        st=(c.get('status') or {}).get('type',{}).get('state'); 
        if st!='post': continue
    h=[x for x in c['competitors'] if x['homeAway']=='home'][0]; a=[x for x in c['competitors'] if x['homeAway']=='away'][0]
    sc=lambda x:(x.get('score') or {}).get('value') if isinstance(x.get('score'),dict) else x.get('score')
    print(e['date'][:10], e['seasonType']['name'][:25], h['team']['displayName'],'|',a['team']['displayName'], sc(h), sc(a))
