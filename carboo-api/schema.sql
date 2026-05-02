-- ============================================================
-- CARBOO NEXT — Volledig Supabase schema v2
-- ============================================================

CREATE TABLE IF NOT EXISTS carboo_gebruikers (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  naam TEXT NOT NULL, email TEXT NOT NULL,
  rol TEXT NOT NULL DEFAULT 'atleet' CHECK (rol IN ('admin','coach','atleet')),
  credits INTEGER NOT NULL DEFAULT 3,
  aangemaakt TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION public.handle_new_user() RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.carboo_gebruikers (id, naam, email)
  VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email,'@',1)), NEW.email);
  RETURN NEW;
END; $$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

CREATE TABLE IF NOT EXISTS carboo_plannen (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  coach_data JSONB NOT NULL,
  bijgewerkt TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS carboo_credit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  omschrijving TEXT NOT NULL, bedrag INTEGER NOT NULL,
  aangemaakt TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fuelc_profiel (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  geslacht TEXT, leeftijd INTEGER, gewicht_kg NUMERIC, lengte_cm INTEGER,
  activiteit TEXT, doelstelling TEXT, doel_tempo NUMERIC,
  bmr INTEGER, tdee_basis INTEGER, energie_doel INTEGER,
  kh_doel_pct INTEGER DEFAULT 50, eiwit_doel_pct INTEGER DEFAULT 25, vet_doel_pct INTEGER DEFAULT 25,
  eet_patroon TEXT DEFAULT 'Klassiek (3 maaltijden)', momenten_tijden TEXT,
  td_0 BOOLEAN DEFAULT false, td_1 BOOLEAN DEFAULT false, td_2 BOOLEAN DEFAULT false,
  UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS fuelc_trainingen (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  datum DATE NOT NULL, sport TEXT NOT NULL, duur_min INTEGER, afstand_km NUMERIC,
  kcal_verbranding INTEGER, zone_verdeling JSONB, notitie TEXT, starttijd TEXT,
  bron TEXT DEFAULT 'manueel', aangemaakt TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fuelc_zones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  sport TEXT NOT NULL, eenheid TEXT DEFAULT 'hartslag',
  z1_tempo_van NUMERIC, z1_tempo_tot NUMERIC, z1_hs_van INTEGER, z1_hs_tot INTEGER,
  z2_tempo_van NUMERIC, z2_tempo_tot NUMERIC, z2_hs_van INTEGER, z2_hs_tot INTEGER,
  z3_tempo_van NUMERIC, z3_tempo_tot NUMERIC, z3_hs_van INTEGER, z3_hs_tot INTEGER,
  z4_tempo_van NUMERIC, z4_tempo_tot NUMERIC, z4_hs_van INTEGER, z4_hs_tot INTEGER,
  z5_tempo_van NUMERIC, z5_tempo_tot NUMERIC, z5_hs_van INTEGER, z5_hs_tot INTEGER,
  UNIQUE(user_id, sport)
);

CREATE TABLE IF NOT EXISTS fuelc_bibliotheek (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  naam TEXT NOT NULL, categorie TEXT, bron TEXT DEFAULT 'manueel',
  portie_g NUMERIC, portie_label TEXT,
  kcal_100g NUMERIC, kh_100g NUMERIC, suikers_100g NUMERIC, vezels_100g NUMERIC,
  eiwit_100g NUMERIC, vet_100g NUMERIC, verzadigd_100g NUMERIC, natrium_100g NUMERIC,
  kalium_100g NUMERIC, calcium_100g NUMERIC, ijzer_100g NUMERIC, magnesium_100g NUMERIC,
  vitc_100g NUMERIC, vitd_100g NUMERIC, vitb12_100g NUMERIC, omega3_100g NUMERIC,
  gi INTEGER, favoriet BOOLEAN DEFAULT false, notitie TEXT, aangemaakt TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fuelc_dagboek (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  datum DATE NOT NULL, moment INTEGER NOT NULL,
  product_id UUID REFERENCES fuelc_bibliotheek(id) ON DELETE SET NULL,
  naam TEXT NOT NULL, hoeveelheid_g NUMERIC NOT NULL,
  kcal NUMERIC, kh_g NUMERIC, eiwit_g NUMERIC, vet_g NUMERIC,
  vezels_g NUMERIC, suikers_g NUMERIC, verz_g NUMERIC,
  natrium_mg NUMERIC, kalium_mg NUMERIC, calcium_mg NUMERIC, ijzer_mg NUMERIC,
  vitd_mcg NUMERIC, vitb12_mcg NUMERIC, omega3_g NUMERIC,
  gi INTEGER, categorie TEXT, aangemaakt TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fuelc_dagboek_welzijn (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  datum DATE NOT NULL, energie_score INTEGER, stemming INTEGER, stress INTEGER,
  slaap_uur NUMERIC, slaap_kwaliteit INTEGER, spierpijn INTEGER,
  hf_rust INTEGER, hrv INTEGER, honger INTEGER,
  gi_klachten BOOLEAN DEFAULT false, gehydrateerd BOOLEAN DEFAULT true,
  rpe INTEGER, energiek_training BOOLEAN, gewicht_kg NUMERIC,
  UNIQUE(user_id, datum)
);

CREATE TABLE IF NOT EXISTS fuelc_recepten_eigen (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  naam TEXT NOT NULL, type TEXT NOT NULL,
  kcal INTEGER, kh NUMERIC, eiwit NUMERIC, vet NUMERIC, vezels NUMERIC, natrium INTEGER,
  ingredienten JSONB, bereiding TEXT, is_globaal BOOLEAN DEFAULT false,
  aangemaakt TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fuelc_recept_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recept_id UUID NOT NULL REFERENCES fuelc_recepten_eigen(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
  UNIQUE(recept_id, user_id)
);

CREATE TABLE IF NOT EXISTS fuelc_recept_reacties (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recept_id UUID NOT NULL REFERENCES fuelc_recepten_eigen(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  naam TEXT, bericht TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fuelc_dagmenu (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  naam TEXT NOT NULL, momenten JSONB NOT NULL,
  is_globaal BOOLEAN DEFAULT false, aangemaakt TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS carboo_gut_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  sport TEXT, niveau TEXT, ervaring TEXT, test_discipline TEXT DEFAULT 'Beide',
  producten JSONB DEFAULT '[]', target_kh INTEGER DEFAULT 60,
  huidige_inname INTEGER DEFAULT 0, eetmomenten INTEGER DEFAULT 2,
  actieve_fase TEXT, bijgewerkt TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS carboo_gut_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES carboo_gebruikers(id) ON DELETE CASCADE,
  week_nr INTEGER NOT NULL, score INTEGER, symptoom TEXT, int_uitg TEXT,
  temp INTEGER, timing_ok TEXT, notitie TEXT, fase TEXT, product TEXT,
  kh_pp INTEGER, porties INTEGER, kh_doel INTEGER,
  progressie TEXT, intensiteit TEXT, ingevuld BOOLEAN DEFAULT false,
  aangemaakt TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, week_nr)
);

-- RLS
ALTER TABLE carboo_gebruikers ENABLE ROW LEVEL SECURITY;
ALTER TABLE carboo_plannen ENABLE ROW LEVEL SECURITY;
ALTER TABLE fuelc_profiel ENABLE ROW LEVEL SECURITY;
ALTER TABLE fuelc_trainingen ENABLE ROW LEVEL SECURITY;
ALTER TABLE fuelc_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE fuelc_bibliotheek ENABLE ROW LEVEL SECURITY;
ALTER TABLE fuelc_dagboek ENABLE ROW LEVEL SECURITY;
ALTER TABLE fuelc_dagboek_welzijn ENABLE ROW LEVEL SECURITY;
ALTER TABLE fuelc_dagmenu ENABLE ROW LEVEL SECURITY;
ALTER TABLE carboo_gut_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE carboo_gut_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "eigen_gebruikers" ON carboo_gebruikers FOR ALL USING (auth.uid() = id);
CREATE POLICY "eigen_plannen" ON carboo_plannen FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "eigen_fuelc_profiel" ON fuelc_profiel FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "eigen_trainingen" ON fuelc_trainingen FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "eigen_zones" ON fuelc_zones FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "eigen_bibliotheek" ON fuelc_bibliotheek FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "eigen_dagboek" ON fuelc_dagboek FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "eigen_welzijn" ON fuelc_dagboek_welzijn FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "eigen_dagmenu" ON fuelc_dagmenu FOR ALL USING (auth.uid() = user_id OR is_globaal = true);
CREATE POLICY "eigen_gut_data" ON carboo_gut_data FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "eigen_gut_logs" ON carboo_gut_logs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "eigen_recepten" ON fuelc_recepten_eigen FOR ALL USING (auth.uid() = user_id OR is_globaal = true);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_trainingen_datum ON fuelc_trainingen(user_id, datum DESC);
CREATE INDEX IF NOT EXISTS idx_dagboek_datum ON fuelc_dagboek(user_id, datum);
CREATE INDEX IF NOT EXISTS idx_welzijn_datum ON fuelc_dagboek_welzijn(user_id, datum);
CREATE INDEX IF NOT EXISTS idx_gut_logs ON carboo_gut_logs(user_id, week_nr);
