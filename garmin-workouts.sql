-- Workouts naar het horloge (GARMIN-WORKOUT-V1): een geplande training uit
-- Carboo wordt via de Garmin Training API als workout aangemaakt en op de
-- dag ingepland. We bewaren Garmin's ids op de training, zodat wijzigen en
-- verwijderen in Carboo ook bij Garmin doorwerken.

alter table fuelc_trainingen add column if not exists garmin_workout_id  bigint;
alter table fuelc_trainingen add column if not exists garmin_schedule_id bigint;
alter table fuelc_trainingen add column if not exists garmin_verstuurd_op timestamptz;
