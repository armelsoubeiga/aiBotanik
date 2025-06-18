import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'aiBotanik',
  description: 'Assistant intelligent pour la phytothérapie et médecine traditionnelle',
  icons: {
    icon: [
      { url: '/favicon.svg' },
      { url: '/icon.svg', sizes: '32x32', type: 'image/svg+xml' },
    ],
    shortcut: '/favicon.svg',
    apple: '/icon.svg',
  }
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  )
}
