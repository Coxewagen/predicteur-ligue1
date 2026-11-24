import json, math
SQ={
"VfB Stuttgart":"Seimen|G|10;Bredlow|G|1;Jeltsch|DC|35;Hendriks|DC|25;Chabot|DC|15;Jaquez|DC|10;Al-Dakhil|DC|3;Zagadou|DC|2;Mittelstädt|DL|18;Vagnoman|DL|12;Assignon|DL|9;Stergiou|DL|2;Stiller|MI|45;Karazor|MI|5;Nartey|MI|10;Spalt|MI|4;Prömel|MI|3.5;El Khannouss|MI|35;Malanga|MI|1.4;Sauer|AT|15;Führich|AT|12;Diehl|AT|1.2;Leweling|AT|40;Tiago Tomás|AT|15;Pejcinovic|BU|25;Demirovic|BU|22;Undav|BU|22",
"Bayern Munich":"Urbig|G|18;Neuer|G|4;Upamecano|DC|75;Tah|DC|28;Kim|DC|20;Ito|DC|18;Brown|DL|50;Davies|DL|45;Stanisic|DL|40;Laimer|DL|32;Boey|DL|7;Pavlovic|MI|90;Kimmich|MI|35;Bischof|MI|45;Ndiaye|MI|8;Musiala|MI|80;Karl|MI|60;Saibari|MI|55;Luis Díaz|AT|70;Olise|AT|180;Gnabry|AT|18;Kane|BU|60",
"Atlético Madrid":"Oblak|G|15;Musso|G|3;Pubill|DC|50;Romero|DC|40;Hancko|DC|35;Le Normand|DC|18;Domínguez|DC|8;Grimaldo|DL|20;Dani Martínez|DL|2.5;Llorente|DL|20;Hjulmand|MI|45;Barrios|MI|70;Mendoza|MI|20;Cardoso|MI|20;Vargas|MI|10;Koke|MI|5;Lee|MI|35;Baena|AT|45;Lookman|AT|40;Ortiz|AT|6;Simeone|AT|40;Alvarez|BU|110;David|BU|30;Sørloth|BU|15",
"Barcelona":"Joan García|G|45;Livakovic|G|4;Cubarsí|DC|100;Eric García|DC|45;Gerard Martín|DC|40;Christensen|DC|8;Balde|DL|40;Koundé|DL|55;Xavi Espart|DL|25;Cancelo|DL|7;Rodri|MI|60;Bernal|MI|40;Pedri|MI|150;Gavi|MI|25;De Jong|MI|25;Fariñas|MI|5;Fermín|MI|110;Olmo|MI|60;Gordon|AT|80;Bisiwu|AT|8;Yamal|AT|220;Adeyemi|AT|40;Bardghji|AT|8;Raphinha|BU|70;Jesus|BU|17",
"Paris Saint-Germain":"Safonov|G|30;Chevalier|G|22;Pacho|DC|80;Zabarnyi|DC|40;Marquinhos|DC|28;Beraldo|DC|22;Nuno Mendes|DL|80;Hernández|DL|18;Digne|DL|6;Hakimi|DL|80;Vitinha|MI|140;Neves|MI|140;Zaïre-Emery|MI|80;Mayulu|MI|40;Fabián|MI|30;Dro|MI|15;Kvaratskhelia|AT|140;Godts|AT|40;Doué|AT|120;Akliouche|AT|50;Dembélé|BU|100;Ferran|BU|55",
"Internazionale":"Martínez|G|10;Provedel|G|3;Bastoni|DC|65;Bisseck|DC|50;Akanji|DC|17;Stones|DC|12;Pavard|DC|12;Dimarco|DL|50;Augusto|DL|23;Spence|DL|35;Stanković|MI|32;Çalhanoğlu|MI|16;Barella|MI|50;Sučić|MI|45;Jones|MI|35;Diouf|MI|30;Zieliński|MI|10;Luis Henrique|DL|20;Lautaro|BU|85;Thuram|BU|50;Esposito|BU|50;Bonny|BU|35",
"AS Roma":"Svilar|G|35;Vásquez|G|0.8;Ndicka|DC|35;Koulierakis|DC|20;Balerdi|DC|18;Ghilardi|DC|18;Mancini|DC|15;Wesley|DL|40;Molina|DL|15;Rensch|DL|8.5;Cristante|MI|7;De Roon|MI|3.2;Koné|MI|60;Pisilli|MI|30;Mora|MI|38;Pellegrini|MI|8;Soulé|AT|35;Dybala|AT|5;Malen|BU|55;Castro|BU|32",
"Manchester United":"Lammens|G|35;Darlow|G|0.2;Martínez|DC|45;Yoro|DC|45;Heaven|DC|30;De Ligt|DC|25;Maguire|DC|8;Shaw|DL|8;Amass|DL|5;Dalot|DL|30;Mazraoui|DL|18;Baleba|MI|65;Santos|MI|45;Ugarte|MI|20;Mainoo|MI|75;Tielemans|MI|40;Bruno|MI|35;Mount|MI|25;Rashford|AT|35;Dorgu|AT|35;Mbeumo|AT|75;Diallo|AT|45;Lacey|AT|12;Cunha|BU|75;Šeško|BU|75;Zirkzee|BU|20",
"Sporting CP":"Rui Silva|G|5;Kaique|G|4;Inácio|DC|35;Debast|DC|25;Ba|DC|20;Quaresma|DC|17;Araújo|DL|40;Zekri|DL|4;Nuno Santos|DL|2;Fresneda|DL|20;Vagiannidis|DL|6;Altimira|MI|25;Andersen|MI|7;Doumbia|MI|20;Simões|MI|15;Lima|MI|3;Zalazar|MI|30;Irankunda|AT|15;Flávio|AT|15;Catamo|AT|35;Guilherme|AT|12;Suárez|BU|30;Ioannidis|BU|16",
"Aston Villa":"Suzuki|G|30;Bizot|G|1.5;Harwood-Bellis|DC|25;Torres|DC|20;Cissé|DC|6;Lindelöf|DC|5;Mings|DC|3;Maatsen|DL|35;Ruggeri|DL|28;Cash|DL|22;Wan-Bissaka|DL|15;Kamara|MI|50;Onana|MI|40;Bogarde|MI|18;Gomes|MI|40;Goretzka|MI|10;Barkley|MI|4;McGinn|MI|13;Manzambi|MI|65;Buendía|MI|16;Garnacho|AT|22;Hemmings|AT|15;Mbaye|AT|50;Alysson|AT|15;Jackson|BU|45;Madjo|BU|22;Abraham|BU|18",
"Lille":"Özer|G|12;Gill|G|7.5;Ngoy|DC|25;Alexsandro|DC|15;Cossier|DC|2.5;Nianzou|DC|1.2;Perraud|DL|7;Verdonk|DL|2.5;Tiago Santos|DL|10;Srdanovic|DL|3;Goffi|DL|1;Mukau|MI|15;Bentaleb|MI|4.5;André|MI|3;Kjærgaard|MI|8;Haraldsson|MI|30;Önal|AT|10;Sahraoui|AT|7;Diaoune|AT|4;Bakwa|AT|28;Mbappé|AT|12;Perrin|AT|5;Ueda|BU|20;Igamane|BU|18;Giroud|BU|0.9",
"Feyenoord Rotterdam":"Ernst|G|6;Kastenmeier|G|1;Mármol|DC|15;Watanabe|DC|8;Kraaijeveld|DC|5;St. Juste|DC|4;Beelen|DC|3;Bos|DL|12;Smal|DL|5.5;López|DL|5;Read|DL|30;Deijl|DL|2;Nieuwkoop|DL|1.5;Targhalline|MI|16;Vanhoutte|MI|7;Zechiël|MI|20;Moder|MI|7;Valente|MI|24;Steijn|MI|11;Nelson|AT|8;Diarra|AT|1.7;Hadj Moussa|AT|28;Borges|AT|3;Ferri|BU|10;Van Persie|BU|5",
"Villarreal":"Luiz Júnior|G|12;Gulácsi|G|1;Veiga|DC|30;Costa|DC|15;Navarro|DC|15;Foyth|DC|8;Romero|DL|25;Cardona|DL|9;Mouriño|DL|20;Freeman|DL|15;Gueye|MI|40;Macià|MI|15;Saliba|MI|15;Comesaña|MI|8;Alassane|MI|5;Moleiro|AT|50;Akhomach|AT|12;Buchanan|AT|12;Pépé|AT|6;Mikautadze|BU|40;Oluwaseyi|BU|7;Ayoze|BU|5;Moreno|BU|2.5"}
OUT={"VfB Stuttgart":["Stiller","Sauer","Vagnoman","Zagadou","Diehl","Jeltsch","Seimen"],"Bayern Munich":["Musiala","Luis Díaz","Gnabry","Saibari","Ndiaye","Pavlovic","Brown","Urbig"],"Atlético Madrid":["Hjulmand","Cardoso","Romero"],"Barcelona":["Christensen","Eric García","Xavi Espart","Koundé","Olmo","Balde"],"Paris Saint-Germain":["Dembélé","Kvaratskhelia","Marquinhos","Nuno Mendes"],"Internazionale":["Bastoni","Jones","Lautaro","Stones","Luis Henrique"],"AS Roma":["Koné","Pellegrini","Svilar","Ndicka","Dybala"],"Manchester United":["Dorgu","Rashford","Šeško","Shaw","Martínez"],"Sporting CP":["Debast","Nuno Santos","Zalazar","Fresneda"],"Aston Villa":["Ruggeri","Wan-Bissaka","Mbaye","Onana","Harwood-Bellis"],"Lille":["Bentaleb","Mbappé","Tiago Santos","Ueda","Igamane","Alexsandro"],"Feyenoord Rotterdam":["Beelen","Bos","Moder","Nieuwkoop","Smal","St. Juste"],"Villarreal":["Akhomach","Alassane","Foyth","Moreno","Mikautadze","Moleiro","Luiz Júnior"]}
DOUBT={}
SLOTS={'G':1,'DC':2,'DL':2,'MI':3,'AT':2,'BU':1}
ADJ={'DC':['DL'],'DL':['DC'],'MI':['AT'],'AT':['MI','BU'],'BU':['AT'],'G':[]}
def xi(pl,excl):
    avail=[p for p in pl if p[0] not in excl]; used=set(); tot=0
    for g,n in SLOTS.items():
        c=sorted([p for p in avail if p[1]==g and p[0] not in used],key=lambda p:-p[2])[:n]
        for p in c: used.add(p[0]); tot+=p[2]
        for _ in range(n-len(c)):   # remplaçant d'un poste voisin à 80 %
            alt=sorted([p for p in avail if p[1] in ADJ[g] and p[0] not in used],key=lambda p:-p[2])
            if alt: used.add(alt[0][0]); tot+=0.8*alt[0][2]
    return tot
res={}
for t,s in SQ.items():
    pl=[(a,b,float(c)) for a,b,c in (x.split('|') for x in s.split(';'))]
    V=xi(pl,set()); W=xi(pl,set(OUT.get(t,[]))); Wd=xi(pl,set(OUT.get(t,[]))|set(DOUBT.get(t,[])))
    Wm=(W+Wd)/2   # incertain = 50 %
    d=max(-40,97.6*math.log(Wm/V)); res[t]=round(d)
    print(f"{t:22s} XI {V:6.0f} M€ -> {Wm:6.0f} M€  Elo {d:+.0f}")
json.dump(res,open('abs_tm.json','w'),ensure_ascii=False)
