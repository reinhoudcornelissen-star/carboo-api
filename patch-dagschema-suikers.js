// patch-dagschema-suikers.js
// 1. Ontdubbelt de productenlijst (databaseitems winnen van NEVO)
// 2. Berekent en bewaart suikers_toegevoegd_g
// 3. Stuurt product_id mee zodat logs aan de bibliotheek gekoppeld zijn
// 4. Behoudt suikers bij "kopieer gisteren" en bij sjablonen
//
// Draaien vanuit de root van carboo-next-v2:
//    node patch-dagschema-suikers.js

const fs = require('fs');
const path = require('path');

const pad = path.join('app', 'app', 'fueling', 'dagschema.tsx');

if (!fs.existsSync(pad)) {
  console.error('FOUT: ' + pad + ' niet gevonden. Draai dit vanuit de projectroot.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('SUIKERSPLITSING-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

// --- helper: exact een keer vervangen --------------------------------------
const wijzigingen = [];
function vervang(naam, zoek, nieuw) {
  const aantal = f.split(zoek).length - 1;
  if (aantal !== 1) {
    console.error('FOUT bij "' + naam + '": anker komt ' + aantal + 'x voor (verwacht 1).');
    console.error('Anker: ' + zoek.split('\n')[0]);
    process.exit(1);
  }
  f = f.replace(zoek, nieuw);
  wijzigingen.push(naam);
}

// --- back-up ---------------------------------------------------------------
const bak = pad + '.bak-suikers';
fs.writeFileSync(bak, f, 'utf8');
console.log('Back-up geschreven: ' + bak);

// --- 1. calc(): toegevoegde suikers meerekenen -----------------------------
vervang(
  'calc() rekent suikers_toegevoegd_g uit',
  '    suikers_g: r(p.suikers),',
  '    suikers_g: r(p.suikers),\n' +
  '    // SUIKERSPLITSING-V1\n' +
  '    suikers_toegevoegd_g: r((p as any).suikers_toegevoegd),'
);

// --- 2. bibliotheek-mapping: veld meenemen ---------------------------------
vervang(
  'bibliotheek-mapping neemt suikers_toegevoegd over',
  '          suikers: p.suikers_100g || 0, verz: p.verzadigd_100g || 0,',
  '          suikers: p.suikers_100g || 0, suikers_toegevoegd: p.suikers_toegevoegd_100g || 0,\n' +
  '          verz: p.verzadigd_100g || 0,'
);

// --- 3. productenlijst ontdubbelen -----------------------------------------
vervang(
  'productenlijst ontdubbeld',
  '  const alleProducten = useMemo(() => [...NEVO_SNEL, ...eigenProducten, ...receptAlsProduct], [eigenProducten, receptAlsProduct])',
  '  // SUIKERSPLITSING-V1: databaseitems winnen van de hardgecodeerde NEVO-lijst\n' +
  '  const alleProducten = useMemo(() => {\n' +
  '    const sleutel = (n: string) => (n || "").trim().toLowerCase()\n' +
  '    const bezet = new Set<string>()\n' +
  '    eigenProducten.forEach((p: any) => {\n' +
  '      bezet.add(sleutel(p.naam))\n' +
  '      if (p.nevo_id) bezet.add(String(p.nevo_id))\n' +
  '    })\n' +
  '    const restNevo = NEVO_SNEL.filter(n => !bezet.has(sleutel(n.naam)) && !bezet.has(n.id))\n' +
  '    return [...eigenProducten, ...restNevo, ...receptAlsProduct]\n' +
  '  }, [eigenProducten, receptAlsProduct])'
);

// --- 4. hoofdpayload: product_id en toegevoegde suikers --------------------
vervang(
  'hoofdpayload stuurt product_id en suikers_toegevoegd_g',
  '        recept_id: (gekozenProduct as any).is_recept ? String((gekozenProduct as any).id).replace(',
  '        suikers_toegevoegd_g: waarden.suikers_toegevoegd_g || 0,\n' +
  '        product_id: (gekozenProduct as any).db_id || null,\n' +
  '        recept_id: (gekozenProduct as any).is_recept ? String((gekozenProduct as any).id).replace('
);

// --- 5. snelknop onderaan: product_id meesturen ----------------------------
vervang(
  'snelknop stuurt product_id mee',
  'body: JSON.stringify({ datum, moment: momentNr, naam: gekozenProduct.naam, hoeveelheid_g: portie, ...waarden })',
  'body: JSON.stringify({ datum, moment: momentNr, naam: gekozenProduct.naam, hoeveelheid_g: portie, ...waarden, product_id: (gekozenProduct as any).db_id || null })'
);

// --- 6. "kopieer gisteren" behoudt suikers ---------------------------------
vervang(
  '"kopieer gisteren" behoudt suikers',
  '            eiwit_g: item.eiwit_g, vet_g: item.vet_g, vezels_g: item.vezels_g || 0,',
  '            eiwit_g: item.eiwit_g, vet_g: item.vet_g, vezels_g: item.vezels_g || 0,\n' +
  '            suikers_g: item.suikers_g || 0, suikers_toegevoegd_g: item.suikers_toegevoegd_g || 0,\n' +
  '            product_id: item.product_id || null, categorie: item.categorie || null,'
);

// --- 7. sjablonen behouden suikers -----------------------------------------
vervang(
  'sjablonen behouden suikers',
  '          eiwit_g: item.eiwit_g, vet_g: item.vet_g, vezels_g: item.vezels_g || 0,',
  '          eiwit_g: item.eiwit_g, vet_g: item.vet_g, vezels_g: item.vezels_g || 0,\n' +
  '          suikers_g: item.suikers_g || 0, suikers_toegevoegd_g: item.suikers_toegevoegd_g || 0,\n' +
  '          product_id: item.product_id || null, categorie: item.categorie || null,'
);

// --- wegschrijven ----------------------------------------------------------
fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - ' + wijzigingen.length + ' wijzigingen toegepast:');
wijzigingen.forEach(w => console.log('  - ' + w));
console.log('');
console.log('Volgende stappen:');
console.log('  npm run build');
console.log('  git add -A && git commit -m "Dagschema bewaart toegevoegde suikers en product_id"');
console.log('  git push origin HEAD:main');
