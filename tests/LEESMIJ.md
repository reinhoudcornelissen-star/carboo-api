# Tests

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
