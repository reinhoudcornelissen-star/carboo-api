# Webpush-diagnose — 28 september 2026

Doel: nagaan of pushmeldingen echt bij klanten aankomen, en waarom abonnementen stilvallen.

## Wat we vonden

- **Afleverketen werkt.** Echte testmelding kwam aan op Android, met titel en tekst.
  `stuur_push()` in main.py stuurt `titel`/`tekst`/`url`/`tag`, en `public/sw.js`
  (carboo-next-v2) leest precies die sleutels.
- **Bereik op 28/09:** 24 rijen, 6 gebruikers (de maker + 5 klanten).
  4 klanten hebben nog minstens één actieve rij, 1 klant heeft alleen een dode rij (410)
  en moet persoonlijk aangesproken worden. `diagnose/broer.py` toont wie.
  "Actief" betekent alleen dat de rij op actief staat, niet dat er iets aankomt.
- **De inactieve rijen zonder foutcode (9) zijn geen verlies.** Elk heeft een actieve
  "broer" bij dezelfde gebruiker. Ze komen van `/api/push/vernieuwen` (adres geroteerd)
  of van `/api/push/afmelden` gevolgd door opnieuw aanzetten (nieuw adres, oude rij blijft).
  Kanttekening: op Android meldt Chrome voor elk toestel "Android 10; K", dus de
  user_agent is daar een zwakke vingerafdruk.
- **Lokaal: Norton 360 onderschept HTTPS.** Python faalt dan met CERTIFICATE_VERIFY_FAILED,
  ook de backend als je die lokaal draait. Oplossing: `lokaal-start.py` (gebruikt de
  certificaten van Windows via `truststore`). Op Render speelt dit niet.
- Bij de testverzending mislukte twee keer de *eerste* verzending naar Microsoft (WNS,
  Edge) met een afgebroken verbinding; volgende gingen wel. Vermoedelijk Norton of de
  verbinding, geen dood toestel. Niet verder onderzocht.

## Nog te doen, in deze volgorde

1. **Toestel opnieuw aanmelden bij elke opening van de app** (frontend, liefst in de
   app-layout; de knop zit nu alleen in `app/app/coach-zone/page.tsx`). Heeft de browser
   een abonnement en is de toestemming "granted", dan stil `POST /api/push/abonneren`.
   Nu kijkt de knop alleen naar de browser: een klant ziet "aan" terwijl de server een
   verouderd of inactief adres heeft. Grootste winst: vangt ook de rotaties die punt 2 mist.
   Helpt alleen klanten die de app nog openen en nog een browserabonnement hebben.
2. **`pushsubscriptionchange` in `public/sw.js` repareren.** Crasht op
   `event.oldSubscription.options` als `oldSubscription` leeg is (gebeurt op Chrome);
   dan wordt `/api/push/vernieuwen` nooit aangeroepen en valt de klant stil weg.
   Opnieuw abonneren met de publieke sleutel van `/api/push/sleutel`.
3. **`/api/push/afmelden` zonder `endpoint` weigeren** (main.py). Nu zet die dan álle
   toestellen van de gebruiker uit. De huidige app stuurt altijd een endpoint mee,
   dus vandaag geen probleem, wel een valkuil.
4. **`/api/push/vernieuwen` werkt zonder login.** Wie een oud adres kent, kan meldingen
   omleiden. Klein risico (adressen zijn geheim), maar op de lijst.

Ook opgemerkt: `stuur_push()` slikt alle fouten behalve 404/410 stil in en schrijft
geen `laatste_fout_op` weg, waardoor problemen in productie onzichtbaar blijven.

## Opnieuw meten (bv. over een maand)

Vanuit carboo-api, met een ingevulde `.env` (SUPABASE_URL, SUPABASE_SERVICE_KEY,
VAPID_PRIVATE_KEY, VAPID_CONTACT; staat in .gitignore):

    python lokaal-start.py diagnose/broer.py        # alleen lezen: bereik per klant
    python lokaal-start.py diagnose/fouten.py       # alleen lezen: telling foutcodes
    python lokaal-start.py push-diagnose.py --droog # alleen lezen
    python lokaal-start.py push-diagnose.py         # ECHTE melding, alleen eigen toestellen
    python lokaal-start.py push-diagnose.py --iedereen  # ECHTE melding naar klanten!

Vergelijkingspunt 28/09: "Klanten (zonder jou): 4 met actieve rij, 1 met alleen inactieve rijen".
