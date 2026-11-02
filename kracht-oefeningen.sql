-- KRACHTPAKKET-V1 (2 november 2026): 28 oefeningen voor het 16-wekenpakket
-- krachttraining (carboo-next-v2/lib/trainingsplan/kracht.ts).
--
-- Elke oefeningnaam in een krachtsessie van het schema moet letterlijk een
-- naam (of naam_nl) in carboo_oefeningen zijn; anders komt ze in de kalender
-- zonder oefening-id en zonder "vorige keer". Van de 28 zijn er 8 plyometrie.
--
-- MET volgens de conventies van de bibliotheek (Compendium 2011): 02020
-- calisthenics stevig 7,5 (zoals Box jump en Burpee al staan), 15550
-- touwspringen 8,8, 02052 squats 5,0, 02054 8-15 herhalingen 3,5, 02024
-- lichte romp 2,8. De voeding rekent met de zwaarte van de sessie, niet met
-- de MET per oefening; die is informatie.
--
-- Globaal (is_globaal true, geen user_id). Een oefening die al bestaat met
-- dezelfde naam wordt overgeslagen, dus dit mag twee keer uitgevoerd worden.
-- Uitvoeren in de SQL-editor van Supabase, vóór of na de deploy.

insert into carboo_oefeningen (naam, naam_nl, spiergroep, type, belasting, met, bron_code, is_globaal)
select v.naam, v.naam_nl, v.spiergroep, v.type, v.belasting, v.met, v.bron_code, true
from (values
  -- plyometrie
  ('Pogo hop',                     'Pogo-sprong',                       'Volledig lichaam', 'compound', 'lichaamsgewicht', 7.5, '02020'),
  ('Jump rope',                    'Touwspringen',                      'Volledig lichaam', 'compound', 'lichaamsgewicht', 8.8, '15550'),
  ('Squat jump',                   'Squat jump',                        'Volledig lichaam', 'compound', 'lichaamsgewicht', 7.5, '02020'),
  ('Split squat jump',             'Split squat jump',                  'Volledig lichaam', 'compound', 'lichaamsgewicht', 7.5, '02020'),
  ('Hurdle hop',                   'Hordensprong',                      'Volledig lichaam', 'compound', 'lichaamsgewicht', 7.5, '02020'),
  ('Single-leg hop',               'Eenbenige hop',                     'Volledig lichaam', 'compound', 'lichaamsgewicht', 7.5, '02020'),
  ('Bounding',                     'Bounding',                          'Volledig lichaam', 'compound', 'lichaamsgewicht', 8.0, '02020'),
  ('Drop jump',                    'Dieptesprong',                      'Volledig lichaam', 'compound', 'lichaamsgewicht', 7.5, '02020'),
  -- vermogen
  ('Jump squat',                   'Jump squat met gewicht',            'Benen',            'compound', 'gewicht',         5.0, '02052'),
  ('Medicine ball throw',          'Medicijnbalworp',                   'Volledig lichaam', 'compound', 'gewicht',         5.0, '02052'),
  -- benen
  ('Glute bridge',                 'Glute bridge',                      'Benen',            'compound', 'lichaamsgewicht', 3.5, '02054'),
  ('Single-leg hip thrust',        'Eenbenige hip thrust',              'Benen',            'compound', 'lichaamsgewicht', 5.0, '02052'),
  ('Reverse lunge',                'Uitvalspas achterwaarts',           'Benen',            'compound', 'gewicht',         5.0, '02052'),
  ('Skater squat',                 'Skater squat',                      'Benen',            'compound', 'lichaamsgewicht', 5.0, '02052'),
  ('Single-leg Romanian deadlift', 'Eenbenige Roemeense deadlift',      'Benen',            'compound', 'gewicht',         5.0, '02052'),
  ('Single-leg leg press',         'Eenbenige beenpers',                'Benen',            'compound', 'gewicht',         5.0, '02052'),
  ('Trap bar deadlift',            'Trap-bar deadlift',                 'Rug',              'compound', 'gewicht',         5.0, '02052'),
  ('Nordic hamstring curl',        'Nordic hamstring curl',             'Benen',            'isolatie', 'lichaamsgewicht', 3.5, '02054'),
  ('Single-leg calf raise',        'Eenbenig kuitheffen',               'Benen',            'isolatie', 'lichaamsgewicht', 3.5, '02054'),
  ('Hip flexion (band or cable)',  'Heupflexie met elastiek of kabel',  'Benen',            'isolatie', 'gewicht',         3.5, '02054'),
  ('Wall sit',                     'Wall sit',                          'Benen',            'isolatie', 'lichaamsgewicht', 2.8, '02024'),
  -- rug en schouders
  ('Band row',                     'Roeien met elastiek',               'Rug',              'compound', 'gewicht',         3.5, '02054'),
  ('Band pull-apart',              'Elastiek uiteentrekken',            'Schouders',        'isolatie', 'gewicht',         2.8, '02024'),
  ('External rotation (band)',     'Externe rotatie met elastiek',      'Schouders',        'isolatie', 'gewicht',         2.8, '02024'),
  -- romp
  ('Side plank',                   'Zijplank',                          'Core',             'isolatie', 'lichaamsgewicht', 2.8, '02024'),
  ('Copenhagen plank',             'Copenhagen plank',                  'Core',             'isolatie', 'lichaamsgewicht', 2.8, '02024'),
  ('Pallof press',                 'Pallof press',                      'Core',             'isolatie', 'gewicht',         2.8, '02024'),
  ('Bird dog',                     'Bird dog',                          'Core',             'isolatie', 'lichaamsgewicht', 2.8, '02024')
) as v(naam, naam_nl, spiergroep, type, belasting, met, bron_code)
where not exists (
  select 1 from carboo_oefeningen o where o.is_globaal and lower(o.naam) = lower(v.naam)
);

-- Controle: moet 28 geven (of minder als er al enkele stonden).
select count(*) from carboo_oefeningen
where is_globaal and naam in ('Pogo hop','Jump rope','Squat jump','Split squat jump','Hurdle hop','Single-leg hop','Bounding',
  'Drop jump','Jump squat','Medicine ball throw','Glute bridge','Single-leg hip thrust','Reverse lunge','Skater squat',
  'Single-leg Romanian deadlift','Single-leg leg press','Trap bar deadlift','Nordic hamstring curl','Single-leg calf raise',
  'Hip flexion (band or cable)','Wall sit','Band row','Band pull-apart','External rotation (band)','Side plank',
  'Copenhagen plank','Pallof press','Bird dog');
