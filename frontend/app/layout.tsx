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
}>) {  return (
    <html lang="fr">
      <head>
        <style>{`
          /* Masquer le badge Next.js Dev Tools */
          [data-nextjs-toast="true"],
          [data-next-badge-root="true"],
          [data-nextjs-dev-tools-button="true"],
          .nextjs-toast {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
          }
        `}</style>
        <script dangerouslySetInnerHTML={{
          __html: `
            // Supprimer le badge Next.js Dev Tools
            function removeNextjsBadge() {
              const selectors = [
                '[data-nextjs-toast="true"]',
                '[data-next-badge-root="true"]',
                '[data-nextjs-dev-tools-button="true"]',
                '.nextjs-toast',
                '[data-next-badge="true"]'
              ];
              
              selectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                  if (el) {
                    el.style.display = 'none';
                    el.style.visibility = 'hidden';
                    el.style.opacity = '0';
                    el.remove();
                  }
                });
              });
            }
            
            // Exécuter immédiatement
            removeNextjsBadge();
            
            // Exécuter quand le DOM est chargé
            document.addEventListener('DOMContentLoaded', removeNextjsBadge);
            
            // Observer les mutations pour supprimer le badge s'il apparaît dynamiquement
            const observer = new MutationObserver(removeNextjsBadge);
            observer.observe(document.body, { childList: true, subtree: true });
            
            // Exécuter périodiquement au cas où
            setInterval(removeNextjsBadge, 100);
          `
        }} />
      </head>
      <body>{children}</body>
    </html>
  )
}
