import './globals.css'
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from 'sonner'
import { LanguageProvider } from '@/components/LanguageProvider';

export const metadata = {
    title: {
        template: '%s | Wali',
        default: "Wali - Micro-assurance pour les Artisans de Cote d'Ivoire",
    },
    description: "La premiere micro-assurance 100% digitale pour les artisans ivoiriens. Assurance sante, protection equipement et couverture contre le vol. Souscription simple via Mobile Money.",
    keywords: ['assurance', 'micro-assurance', 'artisan', "Cote d'Ivoire", 'sante', 'equipement', 'mobile money', 'Abidjan'],
    authors: [{ name: 'Wali Team' }],
    manifest: '/manifest.json',
    appleWebApp: {
        capable: true,
        statusBarStyle: 'default',
        title: 'Wali',
    },
    openGraph: {
        title: 'Wali - Protegez votre activite et votre sante',
        description: 'Assurance accessible pour tous les artisans. A partir de 150 FCFA/mois.',
        url: 'https://wali-pwa.fly.dev',
        siteName: 'Wali',
        locale: 'fr_CI',
        type: 'website',
    },
    twitter: {
        card: 'summary_large_image',
        title: "Wali - L'assurance des artisans",
        description: 'Protegez-vous simplement avec Wali.',
    },
    other: {
        google: 'notranslate'
    }
}

// Separate viewport export (Next.js 14+ best practice)
export const viewport = {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
    themeColor: '#059669',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="fr" translate="no" className="notranslate" suppressHydrationWarning>
            <body>
                <ThemeProvider
                    attribute="class"
                    defaultTheme="light"
                    enableSystem={false}
                    disableTransitionOnChange
                >
                    <LanguageProvider>
                        {children}
                    </LanguageProvider>
                    <Toaster />
                </ThemeProvider>
            </body>
        </html>
    )
}
