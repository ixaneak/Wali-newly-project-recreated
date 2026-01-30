import './globals.css'
import { ThemeProvider } from "@/components/theme-provider"

export const metadata = {
    title: {
        template: '%s | Wali',
        default: 'Wali - Micro-assurance pour les Artisans de Côte d\'Ivoire',
    },
    description: 'La première micro-assurance 100% digitale pour les artisans ivoiriens. Assurance santé, protection équipement et couverture contre le vol. Souscription simple via Mobile Money.',
    keywords: ['assurance', 'micro-assurance', 'artisan', 'Côte d\'Ivoire', 'santé', 'équipement', 'mobile money', 'Abidjan'],
    authors: [{ name: 'Wali Team' }],
    viewport: 'width=device-width, initial-scale=1, maximum-scale=1',
    manifest: '/manifest.json',
    appleWebApp: {
        capable: true,
        statusBarStyle: 'default',
        title: 'Wali',
    },
    openGraph: {
        title: 'Wali - Protégez votre activité et votre santé',
        description: 'Assurance accessible pour tous les artisans. À partir de 150 FCFA/mois.',
        url: 'https://wali-pwa.fly.dev',
        siteName: 'Wali',
        locale: 'fr_CI',
        type: 'website',
    },
    twitter: {
        card: 'summary_large_image',
        title: 'Wali - L\'assurance des artisans',
        description: 'Protégez-vous simplement avec Wali.',
    },
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="fr" suppressHydrationWarning>
            <body>
                <ThemeProvider
                    attribute="class"
                    defaultTheme="light"
                    enableSystem={false}
                    disableTransitionOnChange
                >
                    {children}
                </ThemeProvider>
            </body>
        </html>
    )
}
