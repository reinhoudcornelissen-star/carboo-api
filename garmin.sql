-- Garmin Connect-koppeling (GARMIN-OAUTH-V1): koppelingen, activiteiten,
-- gezondheidsgegevens en de private bucket voor .fit-bestanden.
--
-- De sporter koppelt zelf (OAuth2 PKCE). Toegangssleutels staan versleuteld
-- (AES-256-GCM, sleutel in de omgeving van Render, nooit in de database).
-- Garmin duwt daarna activiteiten en dagwaarden naar de backend.
--
-- RLS staat aan zonder policies: alleen de backend (service key) kan erbij,
-- de app niet rechtstreeks. Ook de bucket is privé.


-- 1. Koppelingen: één rij per sporter
create table if not exists carboo_garmin_koppelingen (
  user_id             uuid primary key,
  garmin_user_id      text unique,                 -- Garmin's eigen id, sleutel voor de push
  access_token        text not null,               -- versleuteld
  refresh_token       text not null,               -- versleuteld
  access_verloopt_op  timestamptz not null,
  refresh_verloopt_op timestamptz,
  rechten             text[] not null default '{}',-- permissions die de sporter gaf
  toestemming_op      timestamptz not null,        -- wanneer het toestemmingsscherm aanvaard werd
  gekoppeld_op        timestamptz not null default now(),
  bijgewerkt_op       timestamptz not null default now(),
  laatste_push_op     timestamptz                  -- laatste bericht van Garmin
);
alter table carboo_garmin_koppelingen enable row level security;


-- 2. Lopende koppelpogingen: state en verifier tussen vertrek en terugkeer.
--    De verifier staat versleuteld. Rijen zijn 15 minuten geldig.
create table if not exists carboo_garmin_koppelpogingen (
  state          text primary key,
  user_id        uuid not null,
  code_verifier  text not null,                   -- versleuteld
  aangemaakt_op  timestamptz not null default now(),
  gebruikt_op    timestamptz
);
alter table carboo_garmin_koppelpogingen enable row level security;


-- 3. Activiteiten zoals Garmin ze meldt (samenvatting + bestand).
--    De training zelf komt in fuelc_trainingen (bron 'garmin'); deze tabel
--    bewaart de details waar we later TSS en vermogen uit rekenen.
create table if not exists carboo_garmin_activiteiten (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null,
  garmin_activity_id  text not null,
  training_id         uuid,                       -- rij in fuelc_trainingen
  naam                text,
  soort               text,                       -- activityType van Garmin
  start_op            timestamptz,
  duur_s              integer,
  afstand_m           numeric,
  kcal                integer,
  gem_hartslag        integer,
  max_hartslag        integer,
  gem_vermogen_w      integer,
  toestel             text,
  handmatig           boolean default false,
  bestand_pad         text,                       -- pad in de bucket, null zolang er geen .fit is
  bestand_bytes       integer,
  kerncijfers         jsonb,                      -- later: NP, TSS, MMP (stap 3)
  ontvangen_op        timestamptz not null default now(),
  unique (user_id, garmin_activity_id)
);
create index if not exists carboo_garmin_activiteiten_user_idx
  on carboo_garmin_activiteiten (user_id, start_op desc);
alter table carboo_garmin_activiteiten enable row level security;


-- 4. Gezondheid per dag: dailies (rustpols, stress, Body Battery, stappen,
--    kcal), sleeps, hrv, userMetrics, bodyComps. De waarden blijven als
--    JSON zoals Garmin ze stuurt; de regels komen later (verbandenlijst).
create table if not exists carboo_garmin_gezondheid (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null,
  soort         text not null
                check (soort in ('dailies', 'sleeps', 'hrv', 'userMetrics', 'bodyComps', 'stressDetails')),
  datum         date not null,
  waarden       jsonb not null,
  ontvangen_op  timestamptz not null default now(),
  unique (user_id, soort, datum)
);
create index if not exists carboo_garmin_gezondheid_user_idx
  on carboo_garmin_gezondheid (user_id, datum desc);
alter table carboo_garmin_gezondheid enable row level security;


-- 5. Trainingen: Garmin-id erbij, zoals strava_activity_id
alter table fuelc_trainingen add column if not exists garmin_activity_id text;
create index if not exists fuelc_trainingen_garmin_idx
  on fuelc_trainingen (user_id, garmin_activity_id);


-- 6. Private bucket voor .fit-bestanden: max 25 MB per bestand
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('garmin-activiteiten', 'garmin-activiteiten', false, 26214400, array['application/octet-stream'])
on conflict (id) do nothing;
