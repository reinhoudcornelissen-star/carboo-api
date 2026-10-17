-- Maaltijdcamera (CAMERA-FOTO-V1): sleutels, foto's en de private bucket.
--
-- De camera (M5Stack Timer Camera X) post een JPEG naar /api/camera/foto met
-- zijn camerasleutel in een header. Hier staat alleen de sha256 van die
-- sleutel: wie de database ziet, kan er de sleutel niet uit terugrekenen.
-- Raak je de camera kwijt: zet actief op false.
--
-- RLS staat aan zonder policies: alleen de backend (service key) kan erbij,
-- de app niet rechtstreeks. Ook de bucket is privé.


-- 1. Sleutels
create table if not exists carboo_camera_sleutels (
  id            uuid primary key default gen_random_uuid(),
  sleutel_hash  text not null unique,          -- sha256 van de sleutel, hex
  user_id       uuid not null,
  naam          text not null,                 -- bv. "Pols"
  actief        boolean not null default true,
  laatst_gezien timestamptz,
  aangemaakt    timestamptz not null default now()
);
alter table carboo_camera_sleutels enable row level security;


-- 2. Foto's. genomen_op = volgens de klok van de camera (ook voor foto's die
--    zonder wifi bewaard werden), ontvangen_op = wanneer de server ze kreeg.
--    Na 7 dagen verdwijnt het bestand uit de bucket; de rij blijft met
--    verwijderd_op ingevuld.
create table if not exists carboo_camera_fotos (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null,
  sleutel_id    uuid references carboo_camera_sleutels(id),
  genomen_op    timestamptz not null default now(),
  ontvangen_op  timestamptz not null default now(),
  pad           text not null,
  bytes         integer,
  status        text not null default 'nieuw'
                check (status in ('nieuw', 'geen_eten', 'verwerkt')),
  maaltijd_id   uuid,
  verwijderd_op timestamptz
);
create index if not exists carboo_camera_fotos_user_idx
  on carboo_camera_fotos (user_id, genomen_op desc);
create index if not exists carboo_camera_fotos_sleutel_idx
  on carboo_camera_fotos (sleutel_id, ontvangen_op desc);
alter table carboo_camera_fotos enable row level security;


-- 3. Private bucket: max 1 MB per foto, alleen JPEG
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('camera-fotos', 'camera-fotos', false, 1048576, array['image/jpeg'])
on conflict (id) do nothing;


-- 4. De camera van de eigenaar. Dit is de HASH van de sleutel; de sleutel zelf
--    staat alleen in carboo-camera/geheimen.h op de pc en op de camera.
insert into carboo_camera_sleutels (sleutel_hash, user_id, naam)
values ('0d1bca7eb63b4a29674c6be9744a9ba12c787c6747fc958294f545eb3e6d6ca0',
        '24605703-c6eb-4194-af80-7a22edec0581', 'Pols')
on conflict (sleutel_hash) do nothing;


-- 5. Controle
select (select count(*) from carboo_camera_sleutels) as sleutels,
       (select count(*) from carboo_camera_fotos)    as fotos,
       (select public from storage.buckets where id = 'camera-fotos') as bucket_publiek;
