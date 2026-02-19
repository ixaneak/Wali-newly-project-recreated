import Link from 'next/link';
import { useLanguage } from '@/components/LanguageProvider';

/**
 * Legal Links Component for Login Screen
 * Displays Terms of Use and Privacy Policy links
 * Compliant with Ivory Coast Law 2013-450
 */
export function LegalLinks() {
    const { t } = useLanguage();

    return (
        <p className="text-xs text-white/50 text-center mt-4">
            {t('legal_text')}{' '}
            <Link
                href="/legal/terms"
                className="text-emerald-400 hover:text-emerald-300 hover:underline font-medium"
            >
                {t('terms')}
            </Link>{' '}
            {t('and')}{' '}
            <Link
                href="/legal/privacy"
                className="text-emerald-400 hover:text-emerald-300 hover:underline font-medium"
            >
                {t('privacy')}
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
