-- Train the Gut: hoogstens een open testmoment per reeks, de status getest,
-- en een set waarden voor intensiteit (laag, matig, hoog, wedstrijdtempo).
-- Draai de blokken in volgorde. Bij elk blok staat of het voor of na de
-- Render-deploy moet.


-- 1. VOOR DE DEPLOY — staat er een check constraint op carboo_gut_testmomenten?
--    Beperkt er een de waarden van status, laat de definitie dan eerst zien:
--    'getest' moet erbij voor de nieuwe backend die status schrijft.
select conname, pg_get_constraintdef(oid) as definitie
from pg_constraint
where conrelid = 'public.carboo_gut_testmomenten'::regclass
  and contype = 'c';


-- 2. NA DE DEPLOY — intensiteit. Eerst alles wat niet in de set zit.
select intensiteit, count(*)
from carboo_gut_testmomenten
where intensiteit is null
   or intensiteit not in ('laag', 'matig', 'hoog', 'wedstrijdtempo')
group by intensiteit;

-- Alleen lage wordt laag. Andere afwijkers eerst bekijken.
update carboo_gut_testmomenten
set intensiteit = 'laag'
where intensiteit = 'lage';


-- 3. NA DE DEPLOY — zelfstandig geteste momenten die nog als open staan.
--    Zonder deze stap botsen ze straks op de unieke index.
select count(*) as open_met_sessie
from carboo_gut_testmomenten m
where m.status = 'open'
  and m.advies_soort is null
  and exists (select 1 from carboo_gut_sessies s where s.testmoment_id = m.id);

update carboo_gut_testmomenten m
set status = 'getest'
where m.status = 'open'
  and m.advies_soort is null
  and exists (select 1 from carboo_gut_sessies s where s.testmoment_id = m.id);


-- 4. NA HET OPRUIMEN — reeksen met meer dan een open moment. Moet leeg zijn,
--    anders lukt de index niet.
select user_id, reeks, count(*) as open_momenten, array_agg(nummer order by nummer) as nummers
from carboo_gut_testmomenten
where status = 'open' and advies_soort is null
group by user_id, reeks
having count(*) > 1;


-- 5. NA STAP 4 — de index. Twee open momenten in een reeks kunnen dan niet
--    meer, ook niet bij een dubbele klik. De backend vangt een botsing op
--    door het open moment terug te geven.
create unique index if not exists carboo_gut_testmomenten_een_open
  on carboo_gut_testmomenten (user_id, reeks)
  where status = 'open' and advies_soort is null;
