import './globals.css'

export const metadata = {
    title: 'Wali',
    description: 'Micro-assurance pour artisans',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="fr">
            <body>{children}</body>
        </html>
    )
}
