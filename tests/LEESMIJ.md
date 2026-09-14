# Tests

Twee scripts, met dezelfde reden van bestaan: er staat een regel op twee
plekken in `main.py`, en zulke paren lopen ooit uit de pas. Ze controleren
daarom niet elke functie apart, maar of het paar op **elk pad hetzelfde zegt**.

Allebei draaien ze zonder database en zonder netwerk. Ze lezen `main.py` via
een pad relatief aan zichzelf en voeren daaruit alles met de `_gut_`-prefix uit
in een eigen namespace. Wat er draait is dus de echte code, geen kopie die kan
verouderen.

```
python tests/test_herstart.py       python tests/test_fasedoorbraak.py
```

---

## test_fasedoorbraak.py

**Wat het bewaakt.** Een coach mag een open testmoment bijsturen, ook omhoog.
Maar een dosis op of boven de grens laat de beslisboom het doel als bereikt
beschouwen, en dan slaat het protocol de hele opbouw over.

- `_gut_coach_fasedoorbraak` zegt **vooraf** of dat gaat gebeuren. Schrijft
  niets. Het coachscherm maakt er zijn bevestiging van.
- `beoordeel_testmoment` besluit **achteraf** dat het gebeurt, met
  `_gut_stap_omhoog(doel, grens) <= doel` → `fase_bevestiging`.

**Waarom dat gevaarlijk is.** Lopen ze uit de pas, dan waarschuwt het scherm
voor een doorbraak die niet komt, óf kort een coach het protocol af zonder dat
iemand het zei. Dat tweede is het ergste: een sporter die van 60 naar 120
springt en slaagt, staat in een klap in de bevestigingsfase met zijn opbouw
overgeslagen — en een darmtrainingsprotocol bestaat juist om die opbouw af te
dwingen. Niemand merkt het tot het gebeurd is.

**Wat het niet bewaakt.** De twee gevallen buiten de opbouw — een dosis in de
bevestiging en in de wedstrijdsimulatie — worden niet werkelijk tegen de
beslisboom gelegd. Daar zet de test `False` omdat de fase daar niet door de
dosis gestuurd wordt. Dat klopt vandaag (`beoordeel_testmoment` gaat in de
bevestiging rechtstreeks naar `fase_wedstrijd`, ongeacht de dosis), maar het is
een aanname in de test en geen meting. Verandert dat ooit, dan blijft dit
script groen terwijl de vaststeller ernaast zit. De vier gevallen ín de
opbouw, waar het werkelijk om gaat, worden wél echt vergeleken.

**Draai het** bij elke wijziging aan `_gut_coach_fasedoorbraak`, aan de
fasebeslissing in `beoordeel_testmoment`, of aan `_gut_stap_omhoog`,
`_gut_doel`, `_gut_protocol_doel` of `GUT_PLAFOND`.

---

## test_herstart.py

**Wat het bewaakt.** In `main.py` staan twee functies die dezelfde vraag
beantwoorden: begint er een nieuwe testreeks als de sporter zijn profiel
opslaat?

- `_gut_herstart_nodig` **stelt vast** of er een herstart komt. Schrijft niets.
  Het scherm maakt van dat antwoord een bevestiging.
- `_gut_t1_verzeker` **voert hem uit**, en alleen met `mag_herstarten=True`.

Die twee beslissen op dezelfde reeks controles: stuurt het protocol, is er een
doel nodig, zijn er momenten, bestaat de kolom `reeks`, is de lopende reeks
niet leeg, verschilt het getal van waar de reeks mee begon, en is er al iets
beoordeeld.

**Waarom dat gevaarlijk is.** Lopen ze uit de pas, dan gebeurt er een van twee
dingen:

- het scherm vraagt bevestiging voor een herstart die niet komt, of
- een reeks wordt herstart zonder dat er iets gevraagd is.

Het tweede merkt een sporter pas als zijn opbouw weg is. Een testreeks
weggooien is onomkeerbaar, en het gebeurt op een moment dat niemand ernaar
kijkt: bij het opslaan van een profiel.

Daarom controleert dit script de twee functies niet apart, maar of ze op **elk
pad hetzelfde zeggen**.

## Draaien

```
python tests/test_herstart.py      # vanuit de wortel van de repo
python test_herstart.py            # vanuit deze map
```

Geen database, geen netwerk, geen andere bestanden. Het script leest `main.py`
via een pad relatief aan zichzelf en voert daaruit alles met de `_gut_`-prefix
uit in een eigen namespace. Wat er draait is dus de echte code, geen kopie die
kan verouderen.

Het eindigt met `alles klopt`, of met een opsomming van de fouten en een
afsluitcode die niet nul is.

## Wanneer je het moet draaien

**Altijd als je een van die twee functies aanraakt.** Ook als de wijziging
klein lijkt: een voorwaarde erbij in de ene en niet in de andere is precies de
fout die dit script vangt, en de enige die je niet ziet aan het scherm.

Ook draaien bij een wijziging in `_gut_momenten`, `_gut_protocol_doel` of
`_gut_doel`, want beide functies leunen erop.

## Wat het niet doet

Het bewijst dat de twee functies **nu** gelijk lopen. Het dwingt niet af dat
wie er een wijzigt de andere aanpast — het maakt alleen zichtbaar dát het
misging. De echte oplossing zou één gedeelde bron van waarheid zijn; die is
bewust niet gekozen, omdat een gedeelde functie met een "doe-het-niet-echt"-vlag
de schrijfactie in een tak verstopt.

Het laatste blok van het script, `KAN DEZE TEST ZELF FALEN?`, saboteert
opzettelijk de vaststeller en controleert dat de oneens-melding afgaat. Zonder
die controle is een test die altijd groen is niet te onderscheiden van een test
die niets meet.
