import Link from 'next/link';

/**
 * Legal Links Component for Login Screen
 * Displays Terms of Use and Privacy Policy links
 * Compliant with Ivory Coast Law 2013-450
 */
export function LegalLinks() {
    return (
        <p className="text-sm text-gray-500 text-center mt-4">
            En vous connectant, vous acceptez nos{' '}
            <Link
                href="/legal/terms"
                className="text-[#0D9488] hover:text-[#0F766E] hover:underline font-medium"
            >
                conditions d&apos;utilisation
            </Link>{' '}
            et notre{' '}
            <Link
                href="/legal/privacy"
                className="text-[#0D9488] hover:text-[#0F766E] hover:underline font-medium"
            >
                politique de confidentialité
            </Link>
        </p>
    );
}

/**
 * English version
 */
export function LegalLinksEN() {
    return (
        <p className="text-sm text-gray-500 text-center mt-4">
            By logging in, you agree to our{' '}
            <Link
                href="/legal/terms"
                className="text-[#0D9488] hover:text-[#0F766E] hover:underline font-medium"
            >
                terms of use
            </Link>{' '}
            and our{' '}
            <Link
                href="/legal/privacy"
                className="text-[#0D9488] hover:text-[#0F766E] hover:underline font-medium"
            >
                privacy policy
            </Link>
        </p>
    );
}

export default LegalLinks;
