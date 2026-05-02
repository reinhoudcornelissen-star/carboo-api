import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Carboo — Sports Nutrition Coach',
  description: 'Jouw persoonlijke sportvoeding coach',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="nl">
      <body>{children}</body>
    </html>
  )
}