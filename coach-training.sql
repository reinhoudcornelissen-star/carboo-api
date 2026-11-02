-- COACH-TRAINING-V1 (2 november 2026): de coach in de module Training van zijn klant.
--
-- De sporterschermen Kalender, Plan en Wedstrijden draaien in de coachzone op
-- het account van de klant, via /api/coach/klant/{klant_id}/training/...
-- Dat kan alleen als de sporter het vinkje "Training" voor die coach aanzet,
-- net als bij dagschema, gewicht of Train the Gut. Zones hadden al eigen
-- coachroutes zonder vinkje; die blijven zoals ze zijn.
--
-- Een schema dat de coach maakt krijgt zijn coach_id, zodat de sporter in de
-- tab Plan ziet "gemaakt door je coach". Trainingen die de coach zet krijgen
-- bron 'coach' en coach_id, zoals de losse coachtrainingen al deden.
--
-- Uitvoeren in de SQL-editor van Supabase, VOOR de deploy van de backend:
-- zonder de kolom training zegt elke coachroute 403 "deelt zijn training niet".

-- 1. Het privacyvinkje. Staat uit voor elke bestaande relatie.
alter table carboo_coach_privacy
  add column if not exists training boolean not null default false;

-- 2. Wie het schema maakte (leeg = de sporter zelf).
alter table carboo_trainingsplannen
  add column if not exists coach_id uuid;
