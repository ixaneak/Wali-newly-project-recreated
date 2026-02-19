export const translations = {
    fr: {
        slogan: "Micro-assurance pour les artisans",
        phone_label: "Numéro de téléphone",
        placeholder: "+225 07 07 07 07 07",
        button_send: "Recevoir le code",
        button_sending: "Envoi...",
        help_button: "Problème de connexion ?",
        help_title: "Comment pouvons-nous vous aider ?",
        contact_support: "Contacter le support",
        no_account: "Pas encore de compte ?",
        create_account: "Créer un compte",
        legal_text: "En vous connectant, vous acceptez nos",
        terms: "conditions d'utilisation",
        and: "et notre",
        privacy: "politique de confidentialité",
        copyright: "© 2025 Wali. Tous droits réservés."
    },
    en: {
        slogan: "Micro-insurance for artisans",
        phone_label: "Phone Number",
        placeholder: "+225 07 07 07 07 07",
        button_send: "Get Code",
        button_sending: "Sending...",
        help_button: "Trouble logging in?",
        help_title: "How can we help?",
        contact_support: "Contact Support",
        no_account: "No account yet?",
        create_account: "Create an account",
        legal_text: "By logging in, you agree to our",
        terms: "Terms of Use",
        and: "and our",
        privacy: "Privacy Policy",
        copyright: "© 2025 Wali. All rights reserved."
    },
    ba: { // Baoulé (Using French as fallback for complex terms, localized where possible)
        slogan: "Wali - Assurance pour les artisans",
        phone_label: "O numéros de téléphone",
        placeholder: "+225 07 07 07 07 07",
        button_send: "Gagnez code",
        button_sending: "Envoi...",
        help_button: "Problème de connexion ?",
        help_title: "Anouka ?",
        contact_support: "Appellez nous",
        no_account: "Pas de compte ?",
        create_account: "Créer un compte",
        legal_text: "En vous connectant, vous acceptez nos",
        terms: "conditions",
        and: "et",
        privacy: "règles",
        copyright: "© 2025 Wali."
    },
    di: { // Dioula (Using French as fallback)
        slogan: "Assurance ka ye artisans ye",
        phone_label: "Téléphone numéros",
        placeholder: "+225 07 07 07 07 07",
        button_send: "Sörö code",
        button_sending: "Naah...",
        help_button: "Tôrô ?",
        help_title: "An ka dèmè ?",
        contact_support: "Aw ni ce",
        no_account: "Compte té ?",
        create_account: "Compte dilan",
        legal_text: "En vous connectant, vous acceptez nos",
        terms: "conditions",
        and: "ni",
        privacy: "règles",
        copyright: "© 2025 Wali."
    }
};

export type Language = keyof typeof translations;
export type TranslationKey = keyof typeof translations.fr;
