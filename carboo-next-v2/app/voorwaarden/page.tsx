export default function VoorwaardenPage() {
  return (
    <div style={{ minHeight: "100vh", background: "#0c0c0c", padding: "80px 20px" }}>
      <div style={{ maxWidth: 720, margin: "0 auto" }}>
        <a href="/login" style={{ fontSize: "0.78rem", color: "#f97316", textDecoration: "none", marginBottom: 32, display: "inline-block" }}>
          ← Terug naar inloggen
        </a>

        <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: "2.5rem", color: "#f5f3ef", letterSpacing: 2, marginBottom: 8 }}>
          Gebruiks<span style={{ color: "#f97316" }}>voorwaarden</span>
        </div>
        <div style={{ fontSize: "0.75rem", color: "#555", marginBottom: 40 }}>Laatst bijgewerkt: mei 2025</div>

        {[
          {
            titel: "1. Algemeen",
            tekst: "Door gebruik te maken van Carboo ga je akkoord met deze gebruiksvoorwaarden. Carboo is een digitaal platform voor sportvoedingsbegeleiding, ontwikkeld voor duursporters. Het platform biedt gepersonaliseerde voedingsadviezen op basis van ingevoerde gegevens."
          },
          {
            titel: "2. Geen medisch advies",
            tekst: "De informatie en adviezen van Carboo zijn uitsluitend bedoeld ter ondersteuning van je sportprestaties en zijn geen vervanging voor professioneel medisch, diëtistisch of voedingskundig advies. Raadpleeg altijd een gekwalificeerde zorgverlener bij gezondheidsproblemen of specifieke medische vragen."
          },
          {
            titel: "3. Gebruik van het platform",
            tekst: "Je mag Carboo uitsluitend gebruiken voor persoonlijke, niet-commerciële doeleinden. Het is niet toegestaan om de inhoud, algoritmen of functies van Carboo te kopiëren, reproduceren of commercieel te exploiteren zonder schriftelijke toestemming."
          },
          {
            titel: "4. Account en beveiliging",
            tekst: "Je bent verantwoordelijk voor de veiligheid van je account en wachtwoord. Carboo is niet aansprakelijk voor schade die voortvloeit uit ongeautoriseerd gebruik van je account. Meld verdachte activiteit onmiddellijk via het contactformulier."
          },
          {
            titel: "5. Abonnement en betaling",
            tekst: "Carboo biedt een gratis proefperiode van 7 dagen. Na de proefperiode bedraagt het abonnement €9,99 per maand. Je kan op elk moment opzeggen via je accountinstellingen. Er worden geen terugbetalingen gedaan voor reeds betaalde periodes."
          },
          {
            titel: "6. Aansprakelijkheid",
            tekst: "Carboo is niet aansprakelijk voor directe of indirecte schade die voortvloeit uit het gebruik van het platform, onjuiste invoer van gegevens, of het opvolgen van voedingsadviezen. Het gebruik van Carboo is op eigen risico."
          },
          {
            titel: "7. Infrastructuur en digitale verstoringen",
            tekst: "Carboo is niet aansprakelijk voor schade, gegevensverlies of onderbrekingen van de dienstverlening als gevolg van technische storingen, serveruitval, netwerkstoringen, cyberaanvallen, hacking, DDoS-aanvallen, datalekken bij derde partijen (zoals hostingproviders of clouddiensten), of andere vormen van digitale of infrastructurele disruptie buiten de directe controle van Carboo. Wij nemen alle redelijke maatregelen om de veiligheid en beschikbaarheid van het platform te waarborgen, maar kunnen geen absolute garantie bieden op ononderbroken of foutloze werking. In geval van een beveiligingsincident zullen wij de betrokken gebruikers zo snel mogelijk informeren conform de wettelijke verplichtingen."
          },
          {
            titel: "8. Overmacht",
            tekst: "Carboo is niet aansprakelijk voor het niet of niet-tijdig nakomen van verplichtingen als gevolg van overmacht, waaronder maar niet beperkt tot: natuurrampen, pandemieën, overheidsmaatregelen, stroomuitval, stakingen, of storingen bij toeleveranciers en derde partijen."
          },
          {
            titel: "9. Wijzigingen",
            tekst: "Carboo behoudt het recht om deze voorwaarden op elk moment te wijzigen. Bij belangrijke wijzigingen word je per e-mail op de hoogte gesteld. Voortgezet gebruik van het platform na wijzigingen geldt als aanvaarding van de nieuwe voorwaarden."
          },
          {
            titel: "10. Contact",
            tekst: "Voor vragen over deze gebruiksvoorwaarden kan je contact opnemen via het platform. We proberen binnen 5 werkdagen te antwoorden."
          },
        ].map(s => (
          <div key={s.titel} style={{ marginBottom: 32 }}>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: "1.1rem", color: "#f97316", letterSpacing: 1, marginBottom: 10 }}>
              {s.titel}
            </div>
            <p style={{ fontSize: "0.9rem", color: "#888", lineHeight: 1.8 }}>{s.tekst}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
