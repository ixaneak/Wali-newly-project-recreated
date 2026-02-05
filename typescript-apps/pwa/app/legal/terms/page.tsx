'use client';

import '../legal.css';
import Link from 'next/link';
import { useState } from 'react';

/**
 * Terms of Use / Conditions Générales d'Utilisation
 * Compliant with Ivory Coast Law 2013-450 and OHADA
 * Last Updated: February 2026
 */
export default function TermsPage() {
    const [language, setLanguage] = useState<'fr' | 'en'>('fr');

    return (
        <div className="legal-container">
            <div className="language-toggle">
                <button
                    className={language === 'fr' ? 'active' : ''}
                    onClick={() => setLanguage('fr')}
                >
                    Français
                </button>
                <button
                    className={language === 'en' ? 'active' : ''}
                    onClick={() => setLanguage('en')}
                >
                    English
                </button>
            </div>

            {language === 'fr' ? <TermsFR /> : <TermsEN />}

            <div className="contact-box">
                <h3>{language === 'fr' ? 'Nous contacter' : 'Contact Us'}</h3>
                <p>
                    <strong>[NOM DE LA SOCIÉTÉ]</strong><br />
                    [ADRESSE COMPLÈTE]<br />
                    Abidjan, Côte d&apos;Ivoire<br />
                    RCCM: [NUMÉRO RCCM]<br />
                    Email: [EMAIL DE CONTACT]<br />
                    Téléphone: [NUMÉRO DE TÉLÉPHONE]
                </p>
            </div>

            <p className="text-sm text-gray-500 mt-8">
                <Link href="/legal/privacy" className="text-[#0D9488] hover:underline">
                    {language === 'fr' ? 'Voir la Politique de Confidentialité' : 'View Privacy Policy'}
                </Link>
            </p>
        </div>
    );
}

function TermsFR() {
    return (
        <>
            <h1>Conditions Générales d&apos;Utilisation</h1>
            <p className="last-updated">Dernière mise à jour : Février 2026</p>
            <p><em>En cas de divergence entre les versions française et anglaise, la version française prévaudra.</em></p>

            <h2>Article 1 – Objet et Acceptation</h2>
            <p>
                Les présentes Conditions Générales d&apos;Utilisation (ci-après « CGU ») régissent l&apos;accès et l&apos;utilisation
                de la plateforme Wali (ci-après « le Service »), éditée par [NOM DE LA SOCIÉTÉ], société de droit ivoirien
                immatriculée au Registre du Commerce et du Crédit Mobilier (RCCM) sous le numéro [NUMÉRO RCCM],
                dont le siège social est situé à [ADRESSE], Abidjan, Côte d&apos;Ivoire.
            </p>
            <p>
                En accédant au Service ou en créant un compte, vous acceptez sans réserve les présentes CGU
                conformément aux dispositions de la Loi n° 2013-450 du 19 juin 2013 relative à la protection
                des données à caractère personnel et aux réglementations de l&apos;Autorité de Régulation des
                Télécommunications/TIC de Côte d&apos;Ivoire (ARTCI).
            </p>

            <h2>Article 2 – Droit Applicable et Juridiction</h2>
            <p>
                Les présentes CGU sont régies par le droit ivoirien, notamment :
            </p>
            <ul>
                <li>La Loi n° 2013-450 du 19 juin 2013 relative à la protection des données à caractère personnel</li>
                <li>L&apos;Acte Uniforme OHADA relatif au Droit Commercial Général</li>
                <li>Le Code de la Propriété Intellectuelle de Côte d&apos;Ivoire</li>
                <li>Les réglementations de l&apos;ARTCI</li>
            </ul>
            <p>
                Tout litige relatif à l&apos;interprétation ou à l&apos;exécution des présentes sera soumis à la compétence
                exclusive des tribunaux compétents d&apos;Abidjan, Côte d&apos;Ivoire, après une tentative de règlement
                amiable de trente (30) jours.
            </p>

            <h2>Article 3 – Capacité et Conditions d&apos;Inscription</h2>
            <p>
                L&apos;utilisation du Service est réservée aux personnes physiques âgées de dix-huit (18) ans révolus
                et jouissant de leur pleine capacité juridique. Les mineurs âgés de treize (13) à dix-sept (17) ans
                peuvent utiliser le Service sous réserve du consentement exprès de leur représentant légal.
            </p>
            <p>
                Lors de l&apos;inscription, vous vous engagez à fournir des informations exactes, complètes et à jour.
                Toute fausse déclaration pourra entraîner la suspension ou la résiliation de votre compte.
            </p>

            <h2>Article 4 – Sécurité du Compte</h2>
            <p>
                Vous êtes seul responsable de la confidentialité de vos identifiants de connexion et de toutes
                les activités effectuées depuis votre compte. Vous vous engagez à :
            </p>
            <ul>
                <li>Ne pas divulguer vos identifiants à des tiers</li>
                <li>Choisir un mot de passe robuste et le modifier régulièrement</li>
                <li>Notifier immédiatement toute utilisation non autorisée de votre compte à [EMAIL DE SUPPORT]</li>
                <li>Vous déconnecter après chaque session, particulièrement sur les appareils partagés</li>
            </ul>

            <h2>Article 5 – Utilisation Acceptable</h2>
            <p>Vous vous engagez à utiliser le Service de manière conforme à la loi ivoirienne et aux présentes CGU. Il est strictement interdit de :</p>
            <ul>
                <li>Collecter, extraire ou stocker des données personnelles d&apos;autres utilisateurs sans autorisation</li>
                <li>Accéder ou tenter d&apos;accéder à des systèmes informatiques ou réseaux sans autorisation</li>
                <li>Transmettre des virus, logiciels malveillants ou tout code nuisible</li>
                <li>Publier des contenus contraires à l&apos;ordre public, aux bonnes mœurs ou aux lois ivoiriennes</li>
                <li>Usurper l&apos;identité d&apos;un tiers ou créer de faux comptes</li>
                <li>Utiliser le Service à des fins frauduleuses ou illicites</li>
                <li>Perturber le fonctionnement normal du Service</li>
            </ul>

            <h2>Article 6 – Propriété Intellectuelle</h2>
            <p>
                L&apos;ensemble des éléments constituant le Service (marques, logos, textes, images, logiciels, bases de données)
                sont protégés par le Code de la Propriété Intellectuelle de Côte d&apos;Ivoire et les conventions internationales
                applicables. Toute reproduction, représentation, modification ou exploitation non autorisée est strictement prohibée.
            </p>

            <h2>Article 7 – Contenu Utilisateur</h2>
            <p>
                En soumettant du contenu sur le Service, vous conservez vos droits de propriété intellectuelle mais
                accordez à [NOM DE LA SOCIÉTÉ] une licence mondiale, non exclusive, gratuite et transférable pour
                utiliser, reproduire, modifier et afficher ce contenu dans le cadre de l&apos;exploitation du Service.
            </p>

            <h2>Article 8 – Limitation de Responsabilité</h2>
            <p>
                Conformément aux standards commerciaux de l&apos;OHADA, [NOM DE LA SOCIÉTÉ] s&apos;engage à fournir le Service
                avec diligence mais ne garantit pas un fonctionnement ininterrompu ou exempt d&apos;erreurs.
                La responsabilité de [NOM DE LA SOCIÉTÉ] est limitée aux dommages directs et prévisibles,
                à l&apos;exclusion de tout dommage indirect.
            </p>

            <h2>Article 9 – Disponibilité du Service</h2>
            <p>
                Le Service est accessible 24h/24, 7j/7, sauf en cas de maintenance programmée ou d&apos;événements
                de force majeure. Les interruptions pour maintenance seront, dans la mesure du possible,
                annoncées à l&apos;avance.
            </p>

            <h2>Article 10 – Suspension et Résiliation</h2>
            <p>
                [NOM DE LA SOCIÉTÉ] se réserve le droit de suspendre ou résilier votre accès au Service,
                sans préavis ni indemnité, en cas de violation des présentes CGU ou de la législation applicable.
                Vous pouvez résilier votre compte à tout moment en contactant [EMAIL DE SUPPORT].
            </p>

            <h2>Article 11 – Règlement des Litiges</h2>
            <p>
                En cas de litige, les parties s&apos;engagent à rechercher une solution amiable pendant une période
                de trente (30) jours. À défaut d&apos;accord, le litige sera porté devant les tribunaux compétents
                d&apos;Abidjan conformément à l&apos;Article 2.
            </p>

            <h2>Article 12 – Modification des CGU</h2>
            <p>
                [NOM DE LA SOCIÉTÉ] peut modifier les présentes CGU à tout moment. Les modifications prendront
                effet après notification aux utilisateurs. L&apos;utilisation continue du Service après notification
                vaut acceptation des nouvelles conditions.
            </p>
        </>
    );
}

function TermsEN() {
    return (
        <>
            <h1>Terms of Use</h1>
            <p className="last-updated">Last Updated: February 2026</p>
            <p><em>In case of discrepancy between the French and English versions, the French version shall prevail.</em></p>

            <h2>Article 1 – Purpose and Acceptance</h2>
            <p>
                These Terms of Use (hereinafter &quot;Terms&quot;) govern access to and use of the Wali platform
                (hereinafter &quot;the Service&quot;), operated by [COMPANY NAME], a company incorporated under
                Ivorian law, registered with the Trade and Personal Property Credit Register (RCCM)
                under number [RCCM NUMBER], with its registered office at [ADDRESS], Abidjan, Ivory Coast.
            </p>
            <p>
                By accessing the Service or creating an account, you unconditionally accept these Terms
                in accordance with Law No. 2013-450 of June 19, 2013 on personal data protection and
                the regulations of the Telecommunications/ICT Regulatory Authority of Ivory Coast (ARTCI).
            </p>

            <h2>Article 2 – Governing Law and Jurisdiction</h2>
            <p>These Terms are governed by Ivorian law, including:</p>
            <ul>
                <li>Law No. 2013-450 of June 19, 2013 on personal data protection</li>
                <li>OHADA Uniform Act on General Commercial Law</li>
                <li>Ivory Coast Intellectual Property Code</li>
                <li>ARTCI regulations</li>
            </ul>
            <p>
                Any dispute relating to the interpretation or execution of these Terms shall be submitted
                to the exclusive jurisdiction of the competent courts of Abidjan, Ivory Coast, after a
                thirty (30) day amicable settlement period.
            </p>

            <h2>Article 3 – Eligibility and Registration</h2>
            <p>
                Use of the Service is reserved for individuals who are eighteen (18) years of age or older
                and have full legal capacity. Minors aged thirteen (13) to seventeen (17) may use the
                Service with express consent from their legal guardian.
            </p>
            <p>
                During registration, you agree to provide accurate, complete, and current information.
                Any false statement may result in suspension or termination of your account.
            </p>

            <h2>Article 4 – Account Security</h2>
            <p>
                You are solely responsible for the confidentiality of your login credentials and all
                activities performed from your account. You agree to:
            </p>
            <ul>
                <li>Not disclose your credentials to third parties</li>
                <li>Choose a strong password and change it regularly</li>
                <li>Immediately notify any unauthorized use of your account to [SUPPORT EMAIL]</li>
                <li>Log out after each session, especially on shared devices</li>
            </ul>

            <h2>Article 5 – Acceptable Use</h2>
            <p>You agree to use the Service in compliance with Ivorian law and these Terms. It is strictly prohibited to:</p>
            <ul>
                <li>Collect, extract, or store personal data of other users without authorization</li>
                <li>Access or attempt to access computer systems or networks without authorization</li>
                <li>Transmit viruses, malware, or any harmful code</li>
                <li>Publish content contrary to public order, morality, or Ivorian laws</li>
                <li>Impersonate another person or create fake accounts</li>
                <li>Use the Service for fraudulent or illegal purposes</li>
                <li>Disrupt the normal operation of the Service</li>
            </ul>

            <h2>Article 6 – Intellectual Property</h2>
            <p>
                All elements constituting the Service (trademarks, logos, texts, images, software, databases)
                are protected by the Ivory Coast Intellectual Property Code and applicable international
                conventions. Any unauthorized reproduction, representation, modification, or exploitation
                is strictly prohibited.
            </p>

            <h2>Article 7 – User Content</h2>
            <p>
                By submitting content on the Service, you retain your intellectual property rights but
                grant [COMPANY NAME] a worldwide, non-exclusive, royalty-free, transferable license to
                use, reproduce, modify, and display such content for the operation of the Service.
            </p>

            <h2>Article 8 – Limitation of Liability</h2>
            <p>
                In accordance with OHADA commercial standards, [COMPANY NAME] commits to providing the
                Service with due diligence but does not guarantee uninterrupted or error-free operation.
                [COMPANY NAME]&apos;s liability is limited to direct and foreseeable damages, excluding any
                indirect damages.
            </p>

            <h2>Article 9 – Service Availability</h2>
            <p>
                The Service is accessible 24/7, except in case of scheduled maintenance or force majeure
                events. Maintenance interruptions will be announced in advance whenever possible.
            </p>

            <h2>Article 10 – Suspension and Termination</h2>
            <p>
                [COMPANY NAME] reserves the right to suspend or terminate your access to the Service,
                without notice or compensation, in case of violation of these Terms or applicable law.
                You may terminate your account at any time by contacting [SUPPORT EMAIL].
            </p>

            <h2>Article 11 – Dispute Resolution</h2>
            <p>
                In case of dispute, the parties agree to seek an amicable solution for a period of
                thirty (30) days. Failing agreement, the dispute shall be brought before the competent
                courts of Abidjan in accordance with Article 2.
            </p>

            <h2>Article 12 – Modification of Terms</h2>
            <p>
                [COMPANY NAME] may modify these Terms at any time. Modifications will take effect after
                notification to users. Continued use of the Service after notification constitutes
                acceptance of the new terms.
            </p>
        </>
    );
}
