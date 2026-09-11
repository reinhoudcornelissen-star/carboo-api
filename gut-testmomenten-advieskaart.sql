-- Train the Gut: de advieskaart per testmoment bewaren.
-- De kaart die de sporter na een beoordeling ziet (scores, regels, wat er
-- volgt) werd nergens bewaard. Een oud testmoment kon hem dus niet meer
-- tonen. Deze kolom bewaart hem zoals hij toen was; hij wordt nooit
-- opnieuw berekend. Veilig om meermaals te draaien.
alter table carboo_gut_testmomenten
  add column if not exists advies_kaart jsonb;

-- Controle: na een beoordeling moet de nieuwste rij een kaart hebben.
select id, advies_soort, advies_kaart is not null as kaart_bewaard, bijgewerkt
from carboo_gut_testmomenten
order by bijgewerkt desc nulls last
limit 5;
