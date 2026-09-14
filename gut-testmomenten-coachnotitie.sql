-- Train the Gut: de coach stuurt een open testmoment bij.
--
-- Een coach tekent geen traject uit -- dat bleek uit de weekopzet, die
-- niemand voorbij week 2 gebruikte -- maar grijpt in op een enkel moment:
-- "doe volgende week nog eens 85, maar met een andere gel."
--
-- Wat hij aanpast staat al in bestaande kolommen: doel_kh_uur, intensiteit,
-- min_duur_min, type_training. door_coach bestaat ook al op deze tabel en
-- werd door niets geschreven; die markeert voortaan DAT een moment
-- bijgestuurd is, en door wie.
--
-- Wat ontbrak is de reden. Die komt in een eigen kolom en niet in advies:
-- dat veld vult de beslisboom na elke beoordeling, en dan zou er straks
-- afwisselend een coachopmerking en een beslisboomtekst in staan.


-- 1. VOOR DE DEPLOY -- de kolom. Leeg is de juiste beginstand: bestaande
--    momenten zijn door niemand bijgestuurd, dus er valt niets in te vullen.
alter table carboo_gut_testmomenten
  add column if not exists coach_notitie text;


-- 2. Controle: de kolom staat er, en door_coach stond er al.
select column_name, data_type, is_nullable
from information_schema.columns
where table_name = 'carboo_gut_testmomenten'
  and column_name in ('coach_notitie', 'door_coach')
order by column_name;


-- 3. Controle: hoeveel momenten kan een coach straks bijsturen?
--    Alleen een OPEN moment in de lopende reeks van een sporter komt in
--    aanmerking. Komt hier nul uit, dan valt er na de deploy niets te
--    proberen tot er een nieuw testmoment openstaat.
with hoogste as (
  select user_id, max(coalesce(reeks, 1)) as reeks_nu
  from carboo_gut_testmomenten
  group by user_id
)
select count(*) as open_momenten_in_lopende_reeks,
       count(distinct t.user_id) as sporters
from carboo_gut_testmomenten t
join hoogste h on h.user_id = t.user_id
              and coalesce(t.reeks, 1) = h.reeks_nu
where t.status = 'open';
