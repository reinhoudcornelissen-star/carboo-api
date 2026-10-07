-- Coachzone: wat de coach aan Train the Gut verandert, komt bij de sporter binnen.
--
-- Een opmerking, bericht of raceplan heeft een eigen ongelezen-teller en telt
-- mee in het rode bolletje bij de clubtab. Een aanpassing aan het lopende
-- gut-protocol, het testplan of een testmoment had dat niet: de sporter merkte
-- er niets van tot hij zelf ging kijken.
--
-- Elke rij hier is één zo'n aanpassing. /api/notificaties toont ze onder het
-- belletje (sleutel coach_signaal_<id>), en zo tellen ze mee in het bolletje.
-- Gelezen loopt via carboo_notificatie_gelezen, net als de andere meldingen.
-- Hoogstens één ongelezen rij per sporter, soort en dag (zie coach_signaal()
-- in main.py): drie keer bijsturen op een middag geeft één melding.
--
-- Alleen de backend leest en schrijft hier, met de service key. RLS staat aan
-- zonder policies, dus de app zelf kan er niet rechtstreeks aan.


-- 1. VOOR OF NA DE DEPLOY -- de code faalt stil zolang de tabel ontbreekt.
create table if not exists carboo_coach_signalen (
  id          uuid primary key default gen_random_uuid(),
  klant_id    uuid not null,
  coach_id    uuid,
  soort       text not null,          -- gut_protocol, gut_testplan, gut_moment
  titel       text not null,
  tekst       text,
  link        text,
  aangemaakt  timestamptz not null default now()
);

create index if not exists carboo_coach_signalen_klant_idx
  on carboo_coach_signalen (klant_id, aangemaakt desc);

alter table carboo_coach_signalen enable row level security;


-- 2. Controle: de tabel staat er, en is nog leeg.
select count(*) as rijen from carboo_coach_signalen;
