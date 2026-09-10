-- Train the Gut: de velden van de evaluatie op sessieniveau.
-- Veilig om meermaals te draaien.
alter table carboo_gut_sessies add column if not exists maagcomfort    smallint;
alter table carboo_gut_sessies add column if not exists smaak_score    smallint;
alter table carboo_gut_sessies add column if not exists externe_factor text;
alter table carboo_gut_sessies add column if not exists testmoment_id  uuid;
-- totaal vocht over de sessie; het uurgemiddelde stond er al voor trainingen
alter table carboo_gut_sessies add column if not exists vocht_ml       integer;

-- Controle: deze vijf moeten terugkomen.
select column_name, data_type
from information_schema.columns
where table_name = 'carboo_gut_sessies'
  and column_name in ('maagcomfort','smaak_score','externe_factor',
                      'testmoment_id','vocht_ml')
order by column_name;
