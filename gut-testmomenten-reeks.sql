-- Train the Gut: de testreeks kan opnieuw beginnen.
-- Verandert de hoogste inname zonder klachten in het profiel, dan start
-- er een nieuwe reeks. De oude momenten blijven staan als geschiedenis,
-- maar tellen niet meer mee in wat de beslisboom afweegt.
-- Veilig om meermaals te draaien.
alter table carboo_gut_testmomenten
  add column if not exists reeks smallint not null default 1;

-- Alles wat er al staat is reeks 1.
update carboo_gut_testmomenten set reeks = 1 where reeks is null;

-- Controle: de kolom moet er staan, en elke rij een reeks hebben.
select reeks, count(*) as momenten
from carboo_gut_testmomenten
group by reeks
order by reeks;
