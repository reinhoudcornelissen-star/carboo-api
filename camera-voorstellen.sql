-- Maaltijdcamera fase 2 (CAMERA-HERKENNING-V1): de logvoorstellen.
--
-- Eén rij = één maaltijd: de camerafoto's die minder dan 20 min uit elkaar
-- liggen. items is wat het model zag, gekoppeld aan de bibliotheek (de
-- voedingswaarden komen daar vandaan, nooit uit het model). Een voorstel komt
-- NIET vanzelf in fuelc_dagboek: de gebruiker bevestigt, past aan of weigert
-- (fase 3). Bij aanpassen wordt eindresultaat bewaard; die correcties gaan bij
-- volgende foto's mee als voorbeeld. tokens_in/tokens_uit/kost_usd houden de
-- echte kosten bij.
--
-- RLS staat aan zonder policies: alleen de backend (service key) kan erbij.


create table if not exists carboo_camera_voorstellen (
  id             uuid primary key default gen_random_uuid(),   -- = maaltijd_id
  user_id        uuid not null,
  begin_op       timestamptz not null,       -- eerste foto van de maaltijd
  einde_op       timestamptz not null,       -- laatste foto
  datum          date not null,              -- Belgische datum
  moment         int,                        -- eetmoment, zoals in het dagboek
  foto_id        uuid references carboo_camera_fotos(id),   -- de gekozen foto
  items          jsonb not null default '[]',
  status         text not null default 'open'
                 check (status in ('open', 'bevestigd', 'aangepast', 'geweigerd')),
  eindresultaat  jsonb,                      -- wat de gebruiker uiteindelijk logde
  model          text,                       -- 'haiku' of 'haiku+sonnet'
  tokens_in      int,
  tokens_uit     int,
  kost_usd       numeric,
  aangemaakt     timestamptz not null default now(),
  afgehandeld_op timestamptz
);
create index if not exists carboo_camera_voorstellen_user_idx
  on carboo_camera_voorstellen (user_id, datum, status);
alter table carboo_camera_voorstellen enable row level security;


-- Controle
select count(*) as voorstellen from carboo_camera_voorstellen;
