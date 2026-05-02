import type { Metadata } from "next"
import { AuthProvider } from "@/lib/auth-context"

export const metadata: Metadata = {
  title: "Carboo — Sports Nutrition Coach",
  description: "Periodiseer je voeding op basis van je trainingsbelasting.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nl">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Instrument+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap"
          rel="stylesheet"
        />
        <style>{`
          *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
          body { font-family: 'Instrument Sans', sans-serif; background: #0c0c0c; color: #f5f3ef; }
          input, button, select, textarea { font-family: inherit; }
          :root {
            --oranje: #f97316;
            --oranje-hover: #ea6c0a;
            --zwart: #0c0c0c;
            --donker: #141414;
            --kaart: #1a1a1a;
            --rand: #2a2a2a;
            --wit: #f5f3ef;
            --grijs: #888;
          }
        `}</style>
      </head>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
