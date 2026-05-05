export default function PrivacyPage() {
  return (
    <div style={{ minHeight: "100vh", background: "#0c0c0c", padding: "80px 20px" }}>
      <div style={{ maxWidth: 720, margin: "0 auto" }}>
        <a href="/login" style={{ fontSize: "0.78rem", color: "#f97316", textDecoration: "none", marginBottom: 32, display: "inline-block" }}>
          ← Terug naar inloggen
        </a>

        <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: "2.5rem", color: "#f5f3ef", letterSpacing: 2, marginBottom: 8 }}>
          Privacy<span style={{ color: "#f97316" }}>beleid</span>
        </div>
        <div style={{ fontSize: "0.75rem", color: "#555", marginBottom: 40 }}>Laatst bijgewerkt: mei 2025</div>

        {[
          {
            titel: "1. Welke gegevens verzamelen we?",
            tekst: "Carboo verzamelt de volgende gegevens: e-mailadres en wachtwoord (voor authenticatie), lichaamsgegevens zoals gewicht, lengte en leeftijd (voor berekeningen), trainingsgegevens en voedingsinformatie die je zelf invoert, en gebruiksdata voor het verbeteren van het platform."
          },
          {
            titel: "2. Waarom verzamelen we deze gegevens?",
            tekst: "Je gegevens worden uitsluitend gebruikt voor het leveren van gepersonaliseerde voedingsadviezen, het bijhouden van je voortgang, het berekenen van je energiebehoeften en macrodoelen, en het verbeteren van de Carboo-algoritmen. We verkopen je gegevens nooit aan derden."
          },
          {
            titel: "3. Hoe bewaren we je gegevens?",
            tekst: "Je gegevens worden veilig opgeslagen via Supabase, een gecertificeerde cloudoplossing met encryptie. Alle verbindingen zijn beveiligd via HTTPS. We bewaren je gegevens zolang je account actief is. Na verwijdering van je account worden je gegevens binnen 30 dagen permanent verwijderd."
          },
          {
            titel: "4. Cookies",
            tekst: "Carboo maakt gebruik van functionele cookies die noodzakelijk zijn voor het werken van de applicatie, zoals het bijhouden van je inlogsessie. We gebruiken geen tracking- of advertentiecookies."
          },
          {
            titel: "5. Jouw rechten",
            tekst: "Je hebt het recht om je persoonlijke gegevens in te zien, te corrigeren of te verwijderen. Je kan ook bezwaar maken tegen bepaalde verwerkingen. Voor het uitoefenen van deze rechten kan je contact met ons opnemen via het platform."
          },
          {
            titel: "6. Derden",
            tekst: "We maken gebruik van de volgende externe diensten: Supabase voor gegevensopslag, Vercel voor hosting van de webapplicatie, en Anthropic voor AI-functionaliteiten (Train the Gut coach). Deze partijen verwerken je gegevens enkel in opdracht van Carboo en conform de GDPR."
          },
          {
            titel: "7. GDPR",
            tekst: "Carboo respecteert de Algemene Verordening Gegevensbescherming (AVG/GDPR). We verwerken je gegevens op basis van jouw toestemming en voor de uitvoering van de dienstverlening. Je kan je toestemming op elk moment intrekken door je account te verwijderen."
          },
          {
            titel: "8. Contact",
            tekst: "Voor vragen over ons privacybeleid of het uitoefenen van je rechten kan je contact opnemen via het platform. We streven ernaar binnen 5 werkdagen te antwoorden."
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
