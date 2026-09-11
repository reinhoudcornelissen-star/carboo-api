-- Train the Gut: waar een testmoment vandaan komt.
-- protocol     het protocol maakte het aan (profiel, advies, weer aanzetten)
-- zelfstandig  de sporter maakte het zelf aan met de plusknop
-- Het label volgt eruit: TP1, TP1b, TP2 voor het protocol, TZ1, TZ2 apart.


-- 1. VOOR DE DEPLOY — de kolom, met de twee toegelaten waarden.
alter table carboo_gut_testmomenten
  add column if not exists bron text not null default 'protocol';

alter table carboo_gut_testmomenten
  drop constraint if exists carboo_gut_testmomenten_bron_check;
alter table carboo_gut_testmomenten
  add constraint carboo_gut_testmomenten_bron_check
  check (bron in ('protocol', 'zelfstandig'));


-- 2. VOOR DE DEPLOY, meteen na stap 1 — bestaande momenten invullen.
--    Regel: status getest wordt zelfstandig, al de rest blijft protocol.
--    Vóór de deploy, zodat de regel alleen bestaande momenten raakt: de
--    nieuwe backend geeft elk nieuw moment zelf zijn bron.
select status, count(*) as momenten
from carboo_gut_testmomenten
group by status
order by status;

update carboo_gut_testmomenten
set bron = 'zelfstandig'
where status = 'getest';

-- Controle
select bron, status, count(*) as momenten
from carboo_gut_testmomenten
group by bron, status
order by bron, status;
