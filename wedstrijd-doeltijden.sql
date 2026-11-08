-- DOELTIJD-V1 (8 november 2026): de doeltijd van een wedstrijd, in seconden,
-- totaal en per onderdeel, bv. {"totaal": 19800, "Zwemmen": 2400, "Fietsen": 10200, "Lopen": 6900}.
-- Veilig om meer dan eens uit te voeren.
alter table carboo_wedstrijden add column if not exists doeltijden jsonb;
