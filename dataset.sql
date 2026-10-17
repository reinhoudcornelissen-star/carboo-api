-- Fotodatabank voor portieherkenning (DATASET-V1).
--
-- Gewogen borden en portieladders, gebruikt als voorbeelden bij de scans van
-- de maaltijdcamera (en later om een eigen model te trainen). Vier bronnen:
--   eigen     een maaltijd die gewogen en gefotografeerd werd
--   reeks     een eigen portieladder (zelfde product, oplopende porties)
--   fotoboek  een stap (A..F) uit een fotoboekbladzijde
--   camera    een bevestigd of verbeterd camera-voorstel, NIET gewogen
-- De testset (1 op 5 van de eigen gewogen borden) wordt nooit als voorbeeld
-- gebruikt, alleen om te meten hoe goed de herkenning is.
-- Deze foto's blijven bewaard (geen opruimregel): dit is blijvend leermateriaal.
-- rechten zegt per bord/reeks wat je met de beelden mag (eigen, fotoboek met
-- toestemming, klant met toestemming...).
--
-- RLS staat aan zonder policies: alleen de backend (service key) kan erbij.


-- 1. Portieladders
create table if not exists carboo_dataset_reeksen (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null,
  naam        text not null,                 -- bv. "Muesli, fotoboek p. 34"
  product_id  uuid,
  recept_id   uuid,
  bron        text not null check (bron in ('reeks', 'fotoboek')),
  rechten     text,
  aangemaakt  timestamptz not null default now()
);
create index if not exists carboo_dataset_reeksen_user_idx on carboo_dataset_reeksen (user_id);
alter table carboo_dataset_reeksen enable row level security;


-- 2. Borden
create table if not exists carboo_dataset_borden (
  id                 uuid primary key default gen_random_uuid(),
  user_id            uuid not null,
  bron               text not null check (bron in ('eigen', 'reeks', 'fotoboek', 'camera')),
  gewogen            boolean not null default true,
  reeks_id           uuid references carboo_dataset_reeksen(id) on delete cascade,
  stap               text,                   -- 'A'..'F' binnen een reeks
  gegeten_op         timestamptz,
  moment             int,
  bord_type          text,                   -- 'plat','diep','kom','bakje','hand'
  bord_cm            numeric,                -- diameter: de meetlat op de foto
  licht              text,                   -- 'daglicht','lamp','donker'
  plaats             text,
  rest_gram          numeric default 0,
  testset            boolean not null default false,
  rechten            text,
  gelogd             boolean not null default false,
  camera_voorstel_id uuid,
  bronmap            text,                   -- bij import: de mapnaam, om dubbels te vermijden
  notitie            text,
  aangemaakt         timestamptz not null default now()
);
create index if not exists carboo_dataset_borden_user_idx on carboo_dataset_borden (user_id, bron);
create unique index if not exists carboo_dataset_borden_bronmap_idx
  on carboo_dataset_borden (user_id, bronmap) where bronmap is not null;
alter table carboo_dataset_borden enable row level security;


-- 3. Wat er op het bord lag (gewogen gram)
create table if not exists carboo_dataset_items (
  id             uuid primary key default gen_random_uuid(),
  bord_id        uuid not null references carboo_dataset_borden(id) on delete cascade,
  product_id     uuid,
  recept_id      uuid,
  naam           text not null,
  gram           numeric not null,
  plaats_op_foto text,                       -- bv. 'kom links', 'bord rechts'
  volgorde       int default 0
);
create index if not exists carboo_dataset_items_bord_idx on carboo_dataset_items (bord_id);
create index if not exists carboo_dataset_items_naam_idx on carboo_dataset_items (lower(naam));
alter table carboo_dataset_items enable row level security;


-- 4. De beelden (ook klaar voor een beeld uit een filmpje, bv. van een bril)
create table if not exists carboo_dataset_fotos (
  id          uuid primary key default gen_random_uuid(),
  bord_id     uuid not null references carboo_dataset_borden(id) on delete cascade,
  pad         text not null,
  toestel     text,                          -- 'pols','gsm','bril','fotoboek','andere'
  hoek        text,                          -- 'boven','schuin','zij','ooghoogte'
  afstand_cm  numeric,
  breedte     int,
  hoogte      int,
  bytes       int,
  video_pad   text,
  frame_ms    int,
  aangemaakt  timestamptz not null default now()
);
create index if not exists carboo_dataset_fotos_bord_idx on carboo_dataset_fotos (bord_id);
alter table carboo_dataset_fotos enable row level security;


-- 5. Private bucket: max 5 MB per beeld, alleen JPEG
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('dataset-fotos', 'dataset-fotos', false, 5242880, array['image/jpeg'])
on conflict (id) do nothing;


-- 6. Controle
select (select count(*) from carboo_dataset_borden) as borden,
       (select count(*) from carboo_dataset_reeksen) as reeksen,
       (select public from storage.buckets where id = 'dataset-fotos') as bucket_publiek;
