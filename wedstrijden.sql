-- Wedstrijden (WEDSTRIJDEN-V1): de wedstrijdkalender van de sporter, zoals
-- in test2perform. Prioriteit A/B/C, eventueel gekoppeld aan een raceplan
-- uit de Race-module (carboo_rapporten, type race_html).
--
-- RLS staat aan zonder policies: alleen de backend (service key) kan erbij.

create table if not exists carboo_wedstrijden (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null,
  datum         date not null,
  naam          text not null,
  prioriteit    text not null default 'B' check (prioriteit in ('A', 'B', 'C')),
  sport         text,
  afstand_km    numeric,
  doel          text,                       -- bv. "sub 3u", "uitrijden"
  notitie       text,
  rapport_id    uuid,                       -- raceplan in carboo_rapporten (optioneel)
  aangemaakt_op timestamptz not null default now(),
  bijgewerkt_op timestamptz not null default now()
);
create index if not exists carboo_wedstrijden_user_idx
  on carboo_wedstrijden (user_id, datum);
alter table carboo_wedstrijden enable row level security;
