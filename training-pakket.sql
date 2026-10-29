-- Training als module (TRAINING-PAKKET-V1): twee nieuwe pakketten in de
-- prijzentabel, en Training gratis erbij voor wie vandaag een actief
-- Fueling-abonnement heeft (vlag op de rij; blijft staan bij verlenging).
--
-- Actie stopzetten: in de admin-tab Prijzen de bundel op niet actief zetten,
-- of hier: update carboo_prijzen set actief = false where id = 'fueling_training';

insert into carboo_prijzen (id, label, prijs, actief)
values ('training', 'Training', 1.99, true),
       ('fueling_training', 'Fueling + Training', 3.99, true)
on conflict (id) do nothing;

alter table carboo_abonnementen add column if not exists bonus_training boolean not null default false;

update carboo_abonnementen
   set bonus_training = true
 where pakket = 'fueling' and status = 'actief';
