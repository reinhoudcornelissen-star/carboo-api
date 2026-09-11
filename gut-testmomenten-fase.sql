-- Train the Gut: de fasen na het opbouwen.
-- opbouw -> (tussentest bij 60 g) -> bevestiging -> wedstrijd -> afgerond
-- Een testmoment zonder fase telt als opbouw. Veilig om meermaals te draaien.
alter table carboo_gut_testmomenten
  add column if not exists fase text;

-- Controle: hoeveel momenten per fase.
select coalesce(fase, 'opbouw (leeg)') as fase, count(*) as momenten
from carboo_gut_testmomenten
group by fase
order by fase;

-- Optioneel, eenmalig. Wie al vastzat op zijn doeldosis heeft een open
-- testmoment dat nog als opbouw staat. Zonder deze stap test hij dat moment
-- eerst nog op lage intensiteit, en komt de bevestiging een sessie later.
-- Vul het e-mailadres in en haal de streepjes weg om het open moment meteen
-- de bevestiging te maken.
--
-- update carboo_gut_testmomenten
-- set fase = 'bevestiging', intensiteit = 'hoog', type_training = 'Intervaltraining'
-- where status = 'open'
--   and advies_soort is null
--   and user_id = (select id from auth.users where email = 'VUL-IN@voorbeeld.be');
