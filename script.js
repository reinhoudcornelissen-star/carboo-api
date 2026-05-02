const foodDb = {
    // ONTBIJT
    "Wit Brood": { unit: "sneden", carbs: 15, grams: 35, type: "vast" },
    "Bruin Brood": { unit: "sneden", carbs: 14, grams: 35, type: "vast" },
    "Sandwich": { unit: "stuks", carbs: 18, grams: 45, type: "vast" },
    "Pistolet": { unit: "stuks", carbs: 26, grams: 60, type: "vast" },
    "Koffiekoek": { unit: "stuks", carbs: 35, grams: 80, type: "vast" },
    "Havermout": { unit: "soeplepels", carbs: 8, grams: 15, type: "vast" },
    "Ontbijtgranen": { unit: "portie", carbs: 30, grams: 40, type: "vast" },
    "Granola": { unit: "soeplepels", carbs: 12, grams: 20, type: "vast" },
    "Muesli": { unit: "soeplepels", carbs: 10, grams: 20, type: "vast" },
    "Banaan": { unit: "stuks", carbs: 25, grams: 150, type: "vast" },
    "Yoghurt": { unit: "ml", carbs: 0.05, grams: 1, type: "vloeibaar" },
    "Platte kaas": { unit: "gram", carbs: 0.04, grams: 1, type: "vast" },
    "Melk": { unit: "ml", carbs: 0.048, grams: 1, type: "vloeibaar" },
    "Sojamelk": { unit: "ml", carbs: 0.03, grams: 1, type: "vloeibaar" },
    "Jam/Confituur": { unit: "koffielp", carbs: 7, grams: 15, type: "vast" },
    "Chocopasta": { unit: "koffielp", carbs: 10, grams: 15, type: "vast" },
    "Honing": { unit: "koffielp", carbs: 6, grams: 10, type: "vast" },
    "Speculoospasta": { unit: "koffielp", carbs: 8, grams: 15, type: "vast" },

    // LUNCH & DINER
        "Ontbijtgranen (40g)": { unit: "portie", carbs: 32, grams: 40, type: "vast" },
    "Rijst (bereid)": { unit: "eetlepels (23g)", carbs: 6.4, grams: 23, type: "vast" },
    "Pasta bijgerecht (150g)": { unit: "portie", carbs: 45, grams: 150, type: "vast" },
    "Pasta hoofdgerecht (300g)": { unit: "portie", carbs: 90, grams: 300, type: "vast" },
    "Aardappelen": { unit: "stuks", carbs: 20, grams: 125, type: "vast" },
    "Quinoa": { unit: "soeplepels", carbs: 11, grams: 45, type: "vast" },
    "Couscous": { unit: "soeplepels", carbs: 10, grams: 40, type: "vast" },
    "Wrap": { unit: "stuks", carbs: 25, grams: 65, type: "vast" },
    "Appelmoes": { unit: "potje", carbs: 22, grams: 100, type: "vast" },
    "Warme groentenmix": { unit: "gram", carbs: 0.08, grams: 1, type: "vast" },
    "Koude groentenmix": { unit: "gram", carbs: 0.05, grams: 1, type: "vast" },

    // TUSSENDOOR
    "Fruit": { unit: "stuks", carbs: 15, grams: 125, type: "vast" },
    "Granenkoek": { unit: "stuks", carbs: 20, grams: 35, type: "vast" },
    "Noten/Zaden": { unit: "handvol", carbs: 4, grams: 25, type: "vast" },
    "Peperkoek": { unit: "sneden", carbs: 18, grams: 30, type: "vast" },
    "Rijstwafel": { unit: "stuks", carbs: 7, grams: 10, type: "vast" },
    "Gedroogde abrikozen": { unit: "stuks", carbs: 4, grams: 8, type: "vast" }
};

const raceProducts = {
    gels: [{ name: "Standard Gel", kh: 25, icon: "🧪" }, { name: "High Carb Gel", kh: 45, icon: "🚀" }],
    cafe: [{ name: "Caffeine Gel", kh: 25, icon: "⚡" }, { name: "Caffeine Gel High", kh: 40, icon: "💥" }],
    vast: [{ name: "Banaan", kh: 25, icon: "🍌" }, { name: "Energiereep", kh: 40, icon: "🍫" }, { name: "Peperkoek", kh: 20, icon: "🍞" }]
};


const momentConfigs = {
    "Ontbijt": { pct: 0.25 },
    "Tussendoor VM": { pct: 0.083 },
    "Lunch": { pct: 0.25 },
    "Tussendoor NM": { pct: 0.083 },
    "Avondmaal": { pct: 0.25 },
    "Avond": { pct: 0.083 }
};

let usedBoosters = { 1: [], 2: [] }; 

function openModule(id) {
    document.getElementById('main-menu').style.display = 'none';
    document.querySelectorAll('.module-section').forEach(s => s.style.display = 'none');
    const target = document.getElementById(id + '-module');
    if (target) {
        target.style.display = 'block';
        if (id === 'carbomax') initCarbomax();
        if (id === 'raceprep') {
            const list = document.getElementById('rp-items-list');
            if (list.children.length === 0) addRaceItemRow();
            updateRacePreview();
        }
    }
}

function initCarbomax() {
    let html = "";
    const ontbijtLijst = ["Wit Brood", "Bruin Brood", "Sandwich", "Pistolet", "Koffiekoek", "Jam/Confituur", "Chocopasta", "Honing", "Speculoospasta", "Havermout", "Ontbijtgranen", "Granola", "Muesli", "Banaan", "Yoghurt", "Platte kaas", "Melk", "Sojamelk"];
    const tussendoorLijst = ["Fruit", "Granenkoek", "Noten/Zaden", "Peperkoek", "Rijstwafel", "Gedroogde abrikozen", "Banaan"];
const maaltijdBronnen = ["Pasta bijgerecht (150g)", "Pasta hoofdgerecht (300g)", "Rijst (bereid)", "Aardappelen", "Wit Brood", "Bruin Brood", "Jam/Confituur", "Honing", "Chocopasta", "Speculoospasta", "Banaan", "Warme groentenmix", "Koude groentenmix"];

    for (let d = 1; d <= 2; d++) {
        html += `<div id="day-container-${d}" class="day-view" style="${d === 2 ? 'display:none' : ''}"><div class="meal-grid">`;
        Object.keys(momentConfigs).forEach(m => {
            html += `<div class="meal-card" id="card-${d}-${m}">
                <div class="card-head" style="display:flex; justify-content:space-between; align-items:center;">
                    <h3>${m.toUpperCase()}</h3>
                    <button class="btn-suggest" onclick="generateRecipe('${m}', ${d})">GEEF SUGGESTIE</button>
                </div>
                <div class="items-list" id="list-${d}-${m}" style="max-height:200px; overflow-y:auto; margin-bottom:10px;">`;

            Object.keys(foodDb).forEach(f => {
                if (m === "Ontbijt" && !ontbijtLijst.includes(f)) return;
                if (m.includes("Tussendoor") && !tussendoorLijst.includes(f)) return;
                if ((m === "Lunch" || m === "Avondmaal") && !maaltijdBronnen.includes(f)) return;
                
                let unitLabel = foodDb[f].unit;
                html += `<div class="item-row" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                    <span style="font-size:0.85rem;">${f}</span>
                    <input type="number" class="p-input" data-dag="${d}" data-moment="${m}" data-food="${f}" placeholder="${unitLabel}" style="width:70px; background:#1e293b; border:1px solid #334155; color:white; text-align:center;">
                </div>`;
            });

            html += `</div>
                <div id="recipe-display-${d}-${m}" class="recipe-suggest-box" style="display:none;"></div>
                <div class="custom-actions">
                    <button class="btn-add-custom" onclick="addCustomRow(${d}, '${m}')">+ Eigen product</button>
                </div>
            </div>`;
        });
        html += `</div></div>`;
    }
    document.getElementById('day-content-container').innerHTML = html;
}


function getBoostTips(tekort, moment, dag) {
    const pool = {
        "Ontbijt": [
            { t: "Extra lepel honing (+6g)", id: "honing" },
            { t: "Glas appelsap (200ml) (+20g)", id: "appelsap" },
            { t: "Extra banaan (+25g)", id: "banaan_extra" },
            { t: "Snee wit brood met jam (+22g)", id: "wit_jam" }
        ],
        "Lunch": [
            { t: "Extra sandwich met stroop (+24g)", id: "stroop" },
            { t: "Beker drinkyoghurt (250ml) (+25g)", id: "drinkyoghurt" },
            { t: "Potje appelmoes (+22g)", id: "appelmoes" },
            { t: "Extra wrap (+25g)", id: "wrap_extra" }
        ],
        "Avondmaal": [
            { t: "Extra schep rijst/pasta (+12g)", id: "rijst_pasta" },
            { t: "Glas limonade (+20g)", id: "limonade" },
            { t: "Schaaltje sorbetijs (+30g)", id: "sorbet" },
            { t: "Wit brood bij de maaltijd (+15g)", id: "brood_extra" }
        ],
        "Tussendoor": [
            { t: "Handvol Winegums (+25g)", id: "winegums" },
            { t: "Blikje frisdrank (330ml) (+35g)", id: "cola" },
            { t: "Twee rijstwafels met honing (+20g)", id: "rijstwafels" },
            { t: "Plak peperkoek (+18g)", id: "peperkoek" },
            { t: "Sportdrank (500ml) (+30g)", id: "isotoon" },
            { t: "Gedroogde dadels (3 stuks) (+18g)", id: "dadels" }
        ]
    };

    let cat = (moment.includes("Tussendoor") || moment === "Avond") ? "Tussendoor" : moment;
    let mogelijkeTips = pool[cat] || pool["Tussendoor"];
    
    let beschikbareTips = mogelijkeTips.filter(tip => !usedBoosters[dag].includes(tip.id));
    if (beschikbareTips.length === 0) { usedBoosters[dag] = []; beschikbareTips = mogelijkeTips; }

    let gekozen = beschikbareTips[Math.floor(Math.random() * beschikbareTips.length)];
    usedBoosters[dag].push(gekozen.id);

    return `• ${gekozen.t}`;
}

function calculatePlan() {
    const gewicht = parseFloat(document.getElementById('gewicht').value) || 0;
    const duur = parseFloat(document.getElementById('duur').value) || 0;
    if (!gewicht) return alert("Vul eerst je gewicht in!");

    usedBoosters = { 1: [], 2: [] }; 
    let factor = duur > 5 ? 12 : (duur > 3 ? 10 : (duur > 1.5 ? 8 : 6));
    const dagTarget = Math.round(gewicht * factor);
    
    let resHtml = `<h2 style="color:#0f172a; text-align:center;">NUTRIFLOW CARB-REPORT</h2><hr>`;

    for (let d = 1; d <= 2; d++) {
        let dagTotaal = 0;
        resHtml += `<div class="res-day"><h3>DAG ${d} OVERZICHT</h3>`;
        
        Object.keys(momentConfigs).forEach(m => {
            let momentCarbs = 0;
            let itemsHTML = "";
            const targetM = Math.round(dagTarget * momentConfigs[m].pct);

            document.querySelectorAll(`.p-input[data-dag="${d}"][data-moment="${m}"]`).forEach(input => {
                const aantal = parseFloat(input.value) || 0;
                if (aantal > 0) {
                    const f = input.dataset.food;
                    const c = aantal * foodDb[f].carbs;
                    momentCarbs += c;
                    itemsHTML += `<li>${aantal}${foodDb[f].unit} ${f} (${Math.round(c)}g)</li>`;
                }
            });

            const customRows = document.getElementById(`list-${d}-${m}`).querySelectorAll('.custom-row-entry');
            customRows.forEach(row => {
                const n = row.querySelector('.custom-name').value;
                const c = parseFloat(row.querySelector('.custom-carbs').value) || 0;
                if (n && c > 0) { momentCarbs += c; itemsHTML += `<li>${n} (Eigen) ⮕ ${c}g</li>`; }
            });

            dagTotaal += momentCarbs;
            const tekort = targetM - momentCarbs;
            const statusColor = tekort <= 5 ? '#22c55e' : '#ef4444';

            resHtml += `<div style="border-left:5px solid ${statusColor}; background:#f8fafc; padding:10px; margin-bottom:10px; color:#1e293b; border-radius:5px;">
                <div style="display:flex; justify-content:space-between; font-weight:bold;">
                    <span>${m}</span> <span>${Math.round(momentCarbs)}g / ${targetM}g</span>
                </div>
                <ul style="font-size:0.8rem; margin:5px 0;">${itemsHTML || "<li>Geen inname gepland</li>"}</ul>`;
            
            if (tekort > 5) {
                resHtml += `<div style="font-size:0.75rem; color:#b91c1c; background:#fee2e2; padding:8px; border-radius:4px; margin-top:5px;">
                    <strong>💡 Booster Tips:</strong><br>${getBoostTips(tekort, m, d)}
                </div>`;
            }
            resHtml += `</div>`;
        });
        resHtml += `<div style="background:#1e293b; color:white; padding:15px; border-radius:8px; text-align:center; font-weight:bold;">
            Totaal Dag ${d}: ${Math.round(dagTotaal)}g / Target: ${dagTarget}g
        </div><br></div>`;
    }
    document.getElementById('result-data').innerHTML = resHtml;
    document.getElementById('result-overlay').style.display = 'block';
    document.getElementById('result-overlay').scrollIntoView({behavior: "smooth"});
}

function generateRecipe(moment, dag) {
    const display = document.getElementById(`recipe-display-${dag}-${moment}`);
    let suggestie = (moment === "Ontbijt") ? { "Pistolet": 2, "Jam/Confituur": 2, "Banaan": 1 } : { "Pasta": 8, "Banaan": 1 };
    display.innerHTML = `<div><b>Suggestie:</b> Voeg items toe.<br><button onclick='applyRecipe(${JSON.stringify(suggestie)}, ${dag}, "${moment}")' style="background:#22c55e; color:white; border:none; padding:5px 10px; border-radius:5px; cursor:pointer; margin-top:5px;">VOEG TOE</button></div>`;
    display.style.display = 'block';
}

function applyRecipe(items, dag, moment) {
    for (let f in items) {
        const input = document.querySelector(`.p-input[data-dag="${dag}"][data-moment="${moment}"][data-food="${f}"]`);
        if (input) input.value = items[f];
    }
    document.getElementById(`recipe-display-${dag}-${moment}`).style.display = 'none';
}

function addCustomRow(dag, moment) {
    const container = document.getElementById(`list-${dag}-${moment}`);
    const div = document.createElement('div');
    div.className = 'item-row custom-row-entry';
    div.style = "display:flex; gap:5px; margin-top:5px;";
    div.innerHTML = `<input type="text" class="custom-name" placeholder="Naam" style="flex:2; background:#0f172a; color:white; border:1px solid #334155; padding:5px; font-size:0.8rem;">
                     <input type="number" class="custom-carbs" placeholder="g" style="flex:1; background:#0f172a; color:white; border:1px solid #334155; padding:5px; font-size:0.8rem;">
                     <button onclick="this.parentElement.remove()" style="color:#ef4444; background:none; border:none; cursor:pointer;">✕</button>`;
    
    const carbInput = div.querySelector('.custom-carbs');
    carbInput.addEventListener('focus', function() {
        alert("Geef de koolhydraten per portie in");
    }, { once: true });
    
    container.appendChild(div);
}

function switchDay(n) {
    document.querySelectorAll('.day-view').forEach(v => v.style.display = 'none');
    document.getElementById(`dag-container-${n}`).style.display = 'block';
    document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
    document.getElementById(`tab${n}`).classList.add('active');
}

function showMenu() { location.reload(); }
function switchDay(n) {
    // 1. Verberg alle dagschermen (Dag 1 en Dag 2)
    document.querySelectorAll('.day-view').forEach(view => {
        view.style.display = 'none';
    });

    // 2. Toon alleen de dag waar je op geklikt hebt
    const geselecteerdeDag = document.getElementById(`day-container-${n}`);
    if (geselecteerdeDag) {
        geselecteerdeDag.style.display = 'block';
    }
    
    // 3. Maak de knoppen visueel actief (kleurtje geven)
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const actieveKnop = document.getElementById(`tab${n}`);
    if (actieveKnop) {
        actieveKnop.classList.add('active');
    }
}
function generateRacePlan() {
    const startStr = document.getElementById('rp-start').value;
    const eindStr = document.getElementById('rp-eind').value;
    
    if (!startStr || !eindStr) return alert("Vul start- en eindtijd in.");

    // 1. Tijd berekenen
    const [h1, m1] = startStr.split(':').map(Number);
    const [h2, m2] = eindStr.split(':').map(Number);
    let startMin = h1 * 60 + m1;
    let eindMin = h2 * 60 + m2;
    if (eindMin <= startMin) eindMin += 1440; 
    let duurMin = eindMin - startMin;

    // 2. Strategie (90g bij >2.5u, anders 60g)
    let targetPerUur = (duurMin / 60) > 2.5 ? 90 : 60;
    let stickerHtml = `<div style="background:black; color:white; padding:10px; font-weight:bold; text-align:center;">STRATEGIE: ${targetPerUur}g KH/u</div>`;

    let uurtellerKH = 0;
    const interval = 20;

    // Hulpfuncties
    const isChecked = (id) => document.getElementById(id) ? document.getElementById(id).checked : false;
    const getKH = (id) => document.getElementById(id) ? parseFloat(document.getElementById(id).value) : 0;

    for (let t = 0; t <= duurMin; t += interval) {
        if (t % 60 === 0) uurtellerKH = 0; // Reset elk uur

        let huidigeTijd = startMin + t;
        let displayTijd = `${Math.floor((huidigeTijd / 60) % 24).toString().padStart(2, '0')}:${(huidigeTijd % 60).toString().padStart(2, '0')}`;
        let actie = "";

        // Hydratatie op het hele uur
        if (t % 60 === 0) {
            if (isChecked('c-drank')) {
                let kh = getKH('kh-drank');
                uurtellerKH += kh;
                actie = `🍼 Sportdrank (${kh}g)`;
            } else if (isChecked('c-water')) {
                actie = "💧 Water (250ml)";
            }
            if (isChecked('c-ors')) actie += " + 🧂 ORS";
        } 
        // Brandstof op 20 of 40 min indien nodig
        else {
            let ruimte = targetPerUur - uurtellerKH;
            if (isChecked('c-vast') && t < duurMin * 0.5 && ruimte >= getKH('kh-vast') - 2) {
                uurtellerKH += getKH('kh-vast'); actie = `🍫 Vast (${getKH('kh-vast')}g)`;
            } else if (isChecked('c-gelcaf') && t > duurMin * 0.75 && ruimte >= getKH('kh-gelcaf') - 2) {
                uurtellerKH += getKH('kh-gelcaf'); actie = `⚡ Caf Gel (${getKH('kh-gelcaf')}g)`;
            } else if (isChecked('c-gel') && ruimte >= getKH('kh-gel') - 2) {
                uurtellerKH += getKH('kh-gel'); actie = `🧪 Gel (${getKH('kh-gel')}g)`;
            }
        }

        if (actie !== "") {
            stickerHtml += `
                <div style="display:flex; border-bottom:1px solid #eee; padding:10px; text-align:left;">
                    <div style="width:60px; font-weight:bold; color:#f97316;">${displayTijd}</div>
                    <div style="flex:1;">${actie}</div>
                    <div style="font-size:0.75rem; color:#64748b;">Uur: ${uurtellerKH}g</div>
                </div>`;
        }
    }

    document.getElementById('sticker-preview').innerHTML = stickerHtml;
    document.getElementById('race-output').style.display = 'block';
}

// Vergeet deze niet, die heb je nodig voor Carbomax navigatie!
function showMenu() {
    document.getElementById('main-menu').style.display = 'grid';
    document.querySelectorAll('.module-section').forEach(s => s.style.display = 'none');
}

function switchDay(d) {
    document.querySelectorAll('.day-view').forEach(v => v.style.display = 'none');
    document.getElementById('day-container-' + d).style.display = 'block';
    document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
    document.getElementById('tab' + d).classList.add('active');
}
// Database voor de Raceprep-items
const raceItemsList = [
    { name: "Kies product...", carbs: 0 },
    { name: "Energy Gel", carbs: 25 },
    { name: "High-Carb Gel", carbs: 45 },
    { name: "Banaan", carbs: 25 },
    { name: "Peperkoek (snede)", carbs: 20 },
    { name: "Energiereep", carbs: 40 }
];

function addRaceItemRow() {
    const container = document.getElementById('rp-dynamic-items');
    const div = document.createElement('div');
    div.style = "display: flex; gap: 5px; align-items: center; background: #334155; padding: 5px; border-radius: 5px;";
    let opts = raceItemsList.map((f, i) => `<option value="${i}">${f.name}</option>`).join('');
    div.innerHTML = `<select class="rp-item-sel" onchange="updateRacePreview()" style="flex:1; color:black;">${opts}</select>
                     <button onclick="this.parentElement.remove(); updateRacePreview();" style="color:red; background:none; border:none; font-weight:bold; cursor:pointer; padding:0 10px;">✕</button>`;
    container.appendChild(div);
}

function updateRacePreview() {
    const temp = parseInt(document.getElementById('rp-temp').value) || 0;
    const dKh = parseInt(document.getElementById('rp-drank-kh').value) || 0;
    const dMl = parseInt(document.getElementById('rp-drank-ml').value) || 0;
    
    let totalKh = dKh;
    let itemsSelected = false;
    document.querySelectorAll('.rp-item-sel').forEach(sel => {
        totalKh += raceFuelDb_Updated[sel.value].carbs;
        if(raceFuelDb_Updated[sel.value].carbs > 0) itemsSelected = true;
    });

    // Dashboard Update
    document.getElementById('dash-kh-label').innerText = totalKh + 'g';
    const bar = document.getElementById('dash-kh-bar');
    const adv = document.getElementById('dash-kh-advies');
    bar.style.width = Math.min((totalKh / 100) * 100, 100) + '%';

    // Wetenschappelijke CARBS check (Target 60-90g/u)
    if(totalKh < 60) {
        adv.innerHTML = "⚠️ <b>Suboptimaal:</b> De wetenschap adviseert 60-90g/u voor duursport. Verhoog je inname.";
        bar.style.background = "#fbbf24";
    } else if(totalKh <= 95) {
        adv.innerHTML = "✅ <b>Optimaal:</b> Je zit perfect in de 60-90g/u range volgens de literatuur.";
        bar.style.background = "#22c55e";
    } else {
        adv.innerHTML = "🚀 <b>Elite:</b> >90g/u vereist darmtraining en een 1:0.8 glucose-fructose mix.";
        bar.style.background = "#3b82f6";
    }

    // ORS & Vocht
    document.getElementById('ors-box').style.display = (temp >= 25) ? 'block' : 'none';
    const warn = document.getElementById('dash-warnings');
    warn.innerHTML = "";
    if(totalKh > 0 && dMl < (totalKh * 8)) {
        warn.innerHTML += `<div style="background:#fee2e2; color:#991b1b; padding:10px; border-radius:8px; font-size:0.8rem;">⚠️ <b>PLAKMAAG:</b> Te weinig vocht t.o.v. carbs. Drink minimaal ${totalKh * 8}ml.</div>`;
    }
    if(itemsSelected) {
        warn.innerHTML += `<div style="background:#e0f2fe; color:#075985; padding:10px; border-radius:8px; font-size:0.8rem;">💧 <b>HYDRATATIE:</b> Neem gels/vast voedsel met max. 250ml water per keer.</div>`;
    }
}

function generateFinalPlan() {
    const start = document.getElementById('rp-start').value;
    const eind = document.getElementById('rp-eind').value;
    const dMl = document.getElementById('rp-drank-ml').value;
    const dKh = document.getElementById('rp-drank-kh').value;
    
    let itemsHtml = "";
    document.querySelectorAll('.rp-item-sel').forEach(sel => {
        const item = raceFuelDb_Updated[sel.value];
        if(item.carbs > 0) itemsHtml += `<span>${item.icon} ${item.name}</span> `;
    });

    let html = `<h4 style="font-weight:bold; margin-bottom:10px;">Uur-schema (${start} - ${eind}):</h4>`;
    html += `<div style="background:#f8fafc; padding:15px; border-radius:10px; border-left: 5px solid #22c55e;">
                <p><strong>Elk uur:</strong></p>
                <ul style="font-size:0.9rem; list-style:none; padding:0;">
                    <li>🥤 ${dMl}ml Sportdrank (${dKh}g KH)</li>
                    <li>🍴 ${itemsHtml}</li>
                    <li style="margin-top:10px; color:#64748b;"><em>Verdeel inname: drink elke 20 min ~150-200ml</em></li>
                </ul>
             </div>`;
    document.getElementById('final-hourly-plan').innerHTML = html;
}
function generateTimeline() {
    const startStr = document.getElementById('rp-start').value;
    const eindStr = document.getElementById('rp-eind').value;
    const temp = parseInt(document.getElementById('rp-temp').value) || 0;
    const dMl = document.getElementById('rp-drank-ml').value;
    const dKh = document.getElementById('rp-drank-kh').value;
    
    if (!startStr || !eindStr) return alert("Vul start- en eindtijd in.");

    // Bereken duur in uren
    const start = new Date(`2026-01-01T${startStr}`);
    const eind = new Date(`2026-01-01T${eindStr}`);
    let diffMs = eind - start;
    if (diffMs < 0) diffMs += 24 * 60 * 60 * 1000;
    const uren = Math.ceil(diffMs / (1000 * 60 * 60));

    // Verzamel geselecteerde extra items
    let extraItemsHtml = "";
    let containsGel = false;
    document.querySelectorAll('.rp-item-sel').forEach(sel => {
        const item = raceFuelDb[sel.value];
        if (item.carbs > 0) {
            extraItemsHtml += `<span style="display:block; margin-top:3px;">${item.icon} ${item.name} (${item.carbs}g KH)</span>`;
            if (item.name.toLowerCase().includes("gel")) containsGel = true;
        }
    });

    let timelineHtml = `<h4 style="font-weight:bold; color:#1e293b; margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;">📋 Jouw Planning per Uur:</h4>`;

    for (let i = 1; i <= uren; i++) {
        const uurTijd = new Date(start.getTime() + (i - 1) * 60 * 60 * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        timelineHtml += `
        <div style="background:#f8fafc; padding:15px; border-radius:10px; border-left: 6px solid #3b82f6; position:relative;">
            <span style="position:absolute; right:10px; top:10px; background:#3b82f6; color:white; padding:2px 8px; border-radius:15px; font-size:0.7rem; font-weight:bold;">UUR ${i}</span>
            <div style="font-weight:bold; font-size:1.1rem; color:#1e293b; margin-bottom:8px;">🕒 Om ${uurTijd}u:</div>
            
            <div style="font-size:0.9rem; color:#334155; line-height:1.5;">
                <div style="margin-bottom:5px;">🥤 <b>${dMl}ml Sportdrank</b> (${dKh}g KH)</div>
                <div style="margin-bottom:10px;">${extraItemsHtml || '<em>Geen extra producten</em>'}</div>
                
                <div style="background:white; padding:8px; border-radius:5px; border:1px solid #e2e8f0; font-size:0.8rem;">
                    <strong style="color:#22c55e;">💡 Aanbeveling:</strong><br>
                    • Verdeel vocht: Drink elke 20 min ~${Math.round(dMl/3)}ml.<br>
                    ${containsGel ? '• 💧 <b>Gels combineren met max 250ml water</b> (geen sportdrank).' : ''}
                    ${temp >= 25 ? '• 🧂 <b>Hoog hitte-risico:</b> Voeg ORS toe aan deze bidon.' : ''}
                </div>
            </div>
        </div>`;
    }

    document.getElementById('race-plan-timeline').innerHTML = timelineHtml;
}

// Hulpmiddelen voor de live-analyse
function updateRacePreview() {
    const temp = parseInt(document.getElementById('rp-temp').value) || 0;
    const dKh = parseInt(document.getElementById('rp-drank-kh').value) || 0;
    let totalKh = dKh;
    document.querySelectorAll('.rp-item-sel').forEach(sel => totalKh += raceFuelDb[sel.value].carbs);

    document.getElementById('dash-kh-label').innerText = totalKh + 'g';
    const bar = document.getElementById('dash-kh-bar');
    const adv = document.getElementById('dash-kh-advies');
    bar.style.width = Math.min((totalKh / 100) * 100, 100) + '%';

    if(totalKh < 60) {
        adv.innerHTML = "⚠️ <b>Suboptimaal:</b> De wetenschap adviseert 60-90g/u.";
        bar.style.background = "#fbbf24";
    } else if(totalKh <= 95) {
        adv.innerHTML = "✅ <b>Optimaal:</b> Perfect conform de literatuur.";
        bar.style.background = "#22c55e";
    } else {
        adv.innerHTML = "🚀 <b>Elite:</b> >90g/u vereist getrainde darmen.";
        bar.style.background = "#3b82f6";
    }
}
function addFuelRow(type) {
    const container = document.getElementById(`list-${type}`);
    const div = document.createElement('div');
    div.style = "display: flex; gap: 8px; margin-bottom: 8px;";
    
    let options = raceProducts[type].map((p, i) => `<option value="${p.kh}|${p.icon}|${p.name}">${p.name} (${p.kh}g)</option>`).join('');
    
    div.innerHTML = `
        <select class="rp-item-${type}" style="flex:1; padding:8px; border-radius:5px; border:1px solid #ddd; font-size:0.9rem;">${options}</select>
        <button onclick="this.parentElement.remove()" style="background:none; border:none; color:#ef4444; font-weight:bold; cursor:pointer; padding:0 10px;">✕</button>
    `;
    container.appendChild(div);
}

// 1. DE CRUCIALE FUNCTIE OM RIJEN TOE TE VOEGEN
function addRow(type) {
    // Zoek de container op basis van het type (drank, gels, cafe, vast)
    const container = document.getElementById(`list-${type}`);
    if (!container) return;

    const div = document.createElement('div');
    div.className = `row-${type}`;
    div.style = "display: flex; gap: 8px; margin-top: 8px; align-items: center;";
    
    // De HTML voor de nieuwe rij
    div.innerHTML = `
        <input type="text" placeholder="Naam product" class="p-name" 
            style="flex:2; padding:8px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.9rem;">
        <input type="number" placeholder="Gram KH" class="p-kh" 
            style="width:80px; padding:8px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.9rem;">
        <button onclick="this.parentElement.remove()" 
            style="background:#fee2e2; color:#ef4444; border:none; padding:8px 12px; border-radius:6px; cursor:pointer; font-weight:bold;">
            ✕
        </button>
    `;
    container.appendChild(div);
}

// 2. DE SMART PLAN GENERATOR
// 1. VOEDINGSMIDDELEN TOEVOEGEN
function addRow(type) {
    const container = document.getElementById(`list-${type}`);
    if (!container) return;

    const div = document.createElement('div');
    div.className = `row-${type}`;
    div.style = "display: flex; gap: 8px; margin-top: 8px; align-items: center;";
    
    div.innerHTML = `
        <input type="text" placeholder="Naam product" class="p-name" 
            style="flex:2; padding:8px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.9rem;">
        <input type="number" placeholder="Gram KH" class="p-kh" 
            style="width:80px; padding:8px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.9rem;">
        <button onclick="this.parentElement.remove()" 
            style="background:#fee2e2; color:#ef4444; border:none; padding:8px 12px; border-radius:6px; cursor:pointer; font-weight:bold;">
            ✕
        </button>
    `;
    container.appendChild(div);
}

// 2. SLIM RACEPLAN GENEREREN
function generateSmartPlan() {
    // 1. INPUTS OPHALEN
    const sport = document.getElementById('rp-sport').value;
    const startStr = document.getElementById('rp-start').value;
    const eindStr = document.getElementById('rp-eind').value;
    const temp = parseInt(document.getElementById('rp-temp').value) || 18;
    const hoogte = parseInt(document.getElementById('rp-height').value) || 0;
    const vochtigheid = parseInt(document.getElementById('rp-hum').value) || 50;
    
    if (!startStr || !eindStr) return alert("Selecteer start- en eindtijd");

    const start = new Date(`2026-01-01T${startStr}`);
    const eind = new Date(`2026-01-01T${eindStr}`);
    let diffMs = eind - start;
    if (diffMs < 0) diffMs += 24 * 60 * 60 * 1000;
    const totaleMinuten = Math.floor(diffMs / (1000 * 60));
    const aantalUren = Math.ceil(totaleMinuten / 60);

    // 2. PRODUCTEN OPHALEN & SORTEREN (Hoogste KH eerst)
    let pool = { drank: [], gels: [], cafe: [], vast: [] };
    ['drank', 'gels', 'cafe', 'vast'].forEach(type => {
        const container = document.getElementById('list-' + type);
        if (container) {
            const rows = container.querySelectorAll('div');
            rows.forEach(row => {
                const inputs = row.querySelectorAll('input');
                if (inputs.length >= 2 && inputs[0].value !== "" && inputs[1].value !== "") {
                    pool[type].push({ 
                        name: inputs[0].value, 
                        kh: parseInt(inputs[1].value) || 0, 
                        type: type 
                    });
                }
            });
        }
        if (type === 'gels' || type === 'vast') {
            pool[type].sort((a, b) => b.kh - a.kh);
        }
    });

    let html = `<h2 style="color:#1e293b; border-bottom:3px solid #3b82f6; padding-bottom:10px; font-weight:900;">SLIM RACEPLAN</h2>`;

    // 3. MELDINGENCENTRUM (HERSTELD)
    if (temp > 28 || (temp > 24 && vochtigheid > 75)) {
        html += `<div style="background:#fef2f2; border-left:5px solid #ef4444; padding:15px; color:#991b1b; margin-bottom:15px; font-size:0.85rem;"><b>⚠️ ORS NODIG:</b> Hitte/vochtigheid te hoog. Gebruik ORS voor zoutbalans.</div>`;
    }
    if (totaleMinuten > 120 && pool.drank.length > 0 && pool.gels.length === 0 && pool.vast.length === 0) {
        html += `<div style="background:#fff7ed; border-left:5px solid #f97316; padding:15px; color:#9a3412; margin-bottom:15px; font-size:0.85rem;"><b>⚠️ COMBINEER:</b> Bij ritten langer dan 2u is enkel sportdrank onvoldoende. Voeg gels of vast voedsel toe.</div>`;
    }
    if (totaleMinuten >= 300 && pool.vast.length === 0) {
        html += `<div style="background:#fff7ed; border-left:5px solid #f97316; padding:15px; color:#9a3412; margin-bottom:15px; font-size:0.85rem;"><b>⚠️ VASTE VOEDING:</b> Bij +5u is vaste voeding cruciaal voor de maag.</div>`;
    }

    // 4. RICHTLIJNEN & VOCHT
    let minT = 0, maxT = 0;
    if (sport === "fietsen") {
        if (totaleMinuten >= 180) { minT = 85; maxT = 110; }
        else if (totaleMinuten >= 120) { minT = 60; maxT = 90; }
        else if (totaleMinuten >= 75) { minT = 30; maxT = 60; }
    }

    let basisVochtUur = temp > 25 ? 800 : (temp > 15 ? 600 : 500);
    let f = ((hoogte / 1000) * 0.15) + (vochtigheid > 70 ? 0.15 : 0);
    let vochtPerMoment = Math.round(((basisVochtUur * (1 + f)) / 3) / 10) * 10;

    let vastIndex = 0;

    // PRE-START
    html += `<div style="background:#f1f5f9; padding:15px; border-radius:15px; margin-bottom:20px; border:2px dashed #3b82f6;"><div style="font-weight:900; color:#3b82f6;">🏁 PRE-START</div><p style="font-size:0.85rem; margin:0;">Kleine slokjes vocht + optionele gel.</p></div>`;

    if (totaleMinuten < 75 && sport === "fietsen") {
        html += `<div style="background:#eff6ff; padding:20px; border-radius:15px; border-left:5px solid #3b82f6; color:#1e3a8a;"><h3 style="margin:0;">⚡ SPRINT PROTOCOL</h3><p style="font-size:0.85rem; margin-top:10px;">Mondspoeling + kleine slokjes water naar behoefte.</p></div>`;
    } else {
        // 5. PLANNING PER UUR
        for (let u = 0; u < aantalUren; u++) {
            let uurKh = 0;
            let isLast = (u === aantalUren - 1);
            let curMin = isLast ? (minT * 0.6) : minT;
            let curMax = isLast ? (maxT * 0.6) : maxT;
            
            let momentItems = { 1: [], 2: [], 3: [] };

            // A. BASIS: SPORTDRANK (Altijd 3 momenten)
            if (pool.drank.length > 0) {
                let d = pool.drank[0];
                [1, 2, 3].forEach(m => {
                    let khM = (d.kh / 500) * vochtPerMoment;
                    momentItems[m].push({ ...d, khM: khM, type: 'drank' });
                    uurKh += khM;
                });
            }

            // B. CAFEÏNE (Enkel uur 2, NOOIT in laatste uur)
            if (u === 1 && !isLast && pool.cafe.length > 0) {
                momentItems[1].push(pool.cafe[0]);
                uurKh += pool.cafe[0].kh;
            }

            // C. VASTE VOEDING (Max 1 per uur, alternerend)
            if (pool.vast.length > 0 && uurKh < curMin) {
                let item = pool.vast[vastIndex % pool.vast.length];
                momentItems[2].push(item);
                uurKh += item.kh;
                vastIndex++;
            }

            // D. GELS (Aanvullen tot doel, hoogste KH eerst)
            let gelSafety = 0;
            while (uurKh < curMin && gelSafety < pool.gels.length) {
                let g = pool.gels[gelSafety % pool.gels.length];
                let m = (momentItems[3].length === 0) ? 3 : 1; 
                momentItems[m].push(g);
                uurKh += g.kh;
                gelSafety++;
            }

            // E. RENDEREN
            html += `<div style="background:#f8fafc; padding:15px; border-radius:15px; margin-bottom:15px; border:1px solid #e2e8f0;">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #3b82f6; padding-bottom:5px; margin-bottom:12px;">
                    <span style="font-weight:900;">UUR ${u+1}</span>
                    <span style="font-size:0.7rem; font-weight:bold; color:#166534;">DOEL: ${Math.round(curMin)}-${Math.round(curMax)}g KH</span>
                </div>`;

            for (let m = 1; m <= 3; m++) {
                let text = "";
                if (isLast && m > 1) {
                    text = `<span style="color:#94a3b8;">Enkel spoelen/water.</span>`;
                } else {
                    let items = momentItems[m];
                    let hasDrink = items.some(i => i.type === 'drank');
                    let waterPrefix = hasDrink ? "" : `🥤 ${vochtPerMoment}ml Water + `;
                    
                    if (items.length === 0) {
                        text = `🥤 ${vochtPerMoment}ml Water`;
                    } else {
                        text = waterPrefix + items.map(i => {
                            if (i.type === 'drank') return `🥤 ${vochtPerMoment}ml <b>${i.name}</b> (${Math.round(i.khM)}g)`;
                            let icoon = i.type === 'vast' ? '🍱' : (i.type === 'cafe' ? '⚡' : '🧪');
                            return `${icoon} <b>${i.name}</b> (${i.kh}g)`;
                        }).join(' + ');
                    }
                }
                html += `<div style="display:flex; gap:12px; margin-bottom:8px; font-size:0.85rem;"><b style="color:#3b82f6; min-width:45px;">${m*20} MIN</b> <span>${text}</span></div>`;
            }
            html += `<div style="margin-top:10px; padding-top:8px; border-top:1px dashed #cbd5e1; font-weight:bold; color:#166534; text-align:right; font-size:0.8rem;">TOTAAL: ${Math.round(uurKh)}g KH</div></div>`;
        }
    }
    document.getElementById('smart-plan-timeline').innerHTML = html;
}

















































