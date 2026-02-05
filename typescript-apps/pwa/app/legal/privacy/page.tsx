'use client';

import '../legal.css';
import Link from 'next/link';
import { useState } from 'react';

/**
 * Privacy Policy / Politique de Confidentialité
 * Compliant with Ivory Coast Law 2013-450 (Personal Data Protection)
 * Aligned with ARTCI regulations
 * Last Updated: February 2026
 */
export default function PrivacyPage() {
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

            {language === 'fr' ? <PrivacyFR /> : <PrivacyEN />}

            <div className="contact-box">
                <h3>{language === 'fr' ? 'Responsable du Traitement' : 'Data Controller'}</h3>
                <p>
                    <strong>[NOM DE LA SOCIÉTÉ]</strong><br />
                    [ADRESSE COMPLÈTE]<br />
                    Abidjan, Côte d&apos;Ivoire<br />
                    RCCM: [NUMÉRO RCCM]<br />
                    Email DPO: [EMAIL DPO]<br />
                    Téléphone: [NUMÉRO DE TÉLÉPHONE]
                </p>
                <h3 className="mt-4">{language === 'fr' ? 'Autorité de Contrôle' : 'Supervisory Authority'}</h3>
                <p>
                    <strong>ARTCI</strong> – Autorité de Régulation des Télécommunications/TIC de Côte d&apos;Ivoire<br />
                    Site web: <a href="https://www.artci.ci" className="text-[#0D9488] hover:underline">www.artci.ci</a><br />
                    Téléphone: +225 20 25 50 00
                </p>
            </div>

            <p className="text-sm text-gray-500 mt-8">
                <Link href="/legal/terms" className="text-[#0D9488] hover:underline">
                    {language === 'fr' ? 'Voir les Conditions Générales d\'Utilisation' : 'View Terms of Use'}
                </Link>
            </p>
        </div>
    );
}

function PrivacyFR() {
    return (
        <>
            <h1>Politique de Confidentialité</h1>
            <p className="last-updated">Dernière mise à jour : Février 2026</p>
            <p><em>En cas de divergence entre les versions française et anglaise, la version française prévaudra.</em></p>

            <h2>Article 1 – Responsable du Traitement</h2>
            <p>
                Le responsable du traitement des données à caractère personnel est [NOM DE LA SOCIÉTÉ],
                société de droit ivoirien immatriculée au RCCM sous le numéro [NUMÉRO RCCM],
                dont le siège social est situé à [ADRESSE], Abidjan, Côte d&apos;Ivoire.
            </p>
            <p>
                Conformément à la Loi n° 2013-450 du 19 juin 2013 relative à la protection des données
                à caractère personnel, nous nous engageons à protéger vos informations personnelles.
            </p>

            <h2>Article 2 – Base Légale du Traitement</h2>
            <p>
                Le traitement de vos données personnelles repose sur votre consentement exprès,
                libre, spécifique, non équivoque et éclairé, conformément à l&apos;Article 23 de la
                Loi n° 2013-450. Ce consentement est recueilli lors de votre inscription au Service.
            </p>
            <p>Nous pouvons également traiter vos données sur la base de :</p>
            <ul>
                <li>L&apos;exécution d&apos;un contrat auquel vous êtes partie</li>
                <li>Le respect d&apos;une obligation légale</li>
                <li>Notre intérêt légitime, lorsqu&apos;il ne porte pas atteinte à vos droits</li>
            </ul>

            <h2>Article 3 – Données Collectées</h2>
            <p>Nous collectons les catégories de données suivantes :</p>

            <h3>3.1 Données d&apos;identification</h3>
            <ul>
                <li>Nom et prénom</li>
                <li>Date de naissance</li>
                <li>Numéro d&apos;identification national (NUI, le cas échéant)</li>
                <li>Photographie d&apos;identité</li>
            </ul>

            <h3>3.2 Données de contact</h3>
            <ul>
                <li>Numéro de téléphone mobile</li>
                <li>Adresse email</li>
                <li>Adresse postale</li>
                <li>Région de résidence</li>
            </ul>

            <h3>3.3 Données techniques</h3>
            <ul>
                <li>Adresse IP</li>
                <li>Type d&apos;appareil et système d&apos;exploitation</li>
                <li>Identifiants de connexion</li>
                <li>Données de géolocalisation (avec votre consentement)</li>
            </ul>

            <h3>3.4 Données d&apos;utilisation</h3>
            <ul>
                <li>Historique des transactions</li>
                <li>Préférences de service</li>
                <li>Journaux d&apos;activité</li>
            </ul>

            <h2>Article 4 – Finalités du Traitement</h2>
            <p>Vos données sont traitées pour les finalités suivantes :</p>
            <ul>
                <li>Création et gestion de votre compte utilisateur</li>
                <li>Fourniture des services de micro-assurance</li>
                <li>Traitement des paiements et transactions</li>
                <li>Gestion des réclamations et sinistres</li>
                <li>Sécurité et prévention de la fraude</li>
                <li>Respect de nos obligations légales et réglementaires</li>
                <li>Amélioration de nos services (avec anonymisation)</li>
                <li>Communication sur nos services (avec votre consentement)</li>
            </ul>

            <h2>Article 5 – Vos Droits (Articles 28-34 de la Loi 2013-450)</h2>
            <p>Conformément à la législation ivoirienne, vous disposez des droits suivants :</p>

            <h3>5.1 Droit d&apos;accès (Article 28)</h3>
            <p>Vous pouvez obtenir confirmation du traitement de vos données et en recevoir une copie.</p>

            <h3>5.2 Droit de rectification (Article 29)</h3>
            <p>Vous pouvez demander la correction de données inexactes ou incomplètes.</p>

            <h3>5.3 Droit d&apos;effacement (Article 30)</h3>
            <p>Vous pouvez demander la suppression de vos données dans les cas prévus par la loi.</p>

            <h3>5.4 Droit d&apos;opposition (Article 31)</h3>
            <p>Vous pouvez vous opposer au traitement de vos données pour des motifs légitimes.</p>

            <h3>5.5 Droit à la portabilité (Article 32)</h3>
            <p>Vous pouvez recevoir vos données dans un format structuré et les transmettre à un autre responsable.</p>

            <h3>5.6 Directives post-mortem (Article 34)</h3>
            <p>Vous pouvez définir des directives concernant le sort de vos données après votre décès.</p>

            <p>Pour exercer ces droits, contactez-nous à [EMAIL DPO].</p>

            <h2>Article 6 – Durée de Conservation</h2>
            <p>Vos données sont conservées conformément aux lignes directrices de l&apos;ARTCI :</p>
            <ul>
                <li>Données de compte : durée de la relation contractuelle + 5 ans</li>
                <li>Données de transaction : 10 ans (obligations comptables et fiscales)</li>
                <li>Données de connexion : 1 an</li>
                <li>Données de prospection : 3 ans après le dernier contact</li>
            </ul>

            <h2>Article 7 – Destinataires des Données</h2>
            <p>Vos données peuvent être communiquées à :</p>
            <ul>
                <li>Notre personnel autorisé (strictement nécessaire)</li>
                <li>Nos prestataires de services (paiement, hébergement, support)</li>
                <li>Les autorités judiciaires ou administratives sur réquisition légale</li>
                <li>Nos partenaires assureurs pour l&apos;exécution des polices</li>
            </ul>

            <h2>Article 8 – Transferts Internationaux</h2>
            <p>
                Vos données ne sont transférées vers des pays tiers que s&apos;ils garantissent un niveau
                de protection équivalent à la législation ivoirienne, conformément à la Loi n° 2013-450.
                En l&apos;absence de décision d&apos;adéquation, nous mettons en place des garanties appropriées.
            </p>

            <h2>Article 9 – Sécurité des Données (Article 19)</h2>
            <p>
                Conformément à l&apos;Article 19 de la Loi n° 2013-450, nous mettons en œuvre des mesures
                techniques et organisationnelles pour protéger vos données :
            </p>
            <ul>
                <li>Confidentialité : accès restreint au personnel autorisé</li>
                <li>Intégrité : contrôles pour prévenir toute altération</li>
                <li>Chiffrement des transmissions réseau (HTTPS/TLS)</li>
                <li>Authentification forte et gestion des accès</li>
                <li>Sauvegardes régulières et plans de continuité</li>
            </ul>

            <h2>Article 10 – Données Sensibles (Article 7)</h2>
            <p>
                Nous ne collectons pas de données sensibles (origine ethnique, opinions politiques,
                convictions religieuses, données de santé, orientation sexuelle) sans votre consentement
                exprès et, le cas échéant, l&apos;autorisation préalable de l&apos;ARTCI.
            </p>

            <h2>Article 11 – Cookies et Technologies de Suivi</h2>
            <p>Nous utilisons des cookies pour :</p>
            <ul>
                <li><strong>Cookies essentiels :</strong> fonctionnement du Service (pas de consentement requis)</li>
                <li><strong>Cookies analytiques :</strong> mesure d&apos;audience (avec votre consentement)</li>
                <li><strong>Cookies fonctionnels :</strong> personnalisation (avec votre consentement)</li>
            </ul>
            <p>Vous pouvez gérer vos préférences via les paramètres de votre navigateur.</p>

            <h2>Article 12 – Réclamation auprès de l&apos;ARTCI</h2>
            <p>
                Si vous estimez que vos droits ne sont pas respectés, vous pouvez introduire une réclamation
                auprès de l&apos;Autorité de Régulation des Télécommunications/TIC de Côte d&apos;Ivoire (ARTCI) :
            </p>
            <ul>
                <li>Site web : <a href="https://www.artci.ci" className="text-[#0D9488]">www.artci.ci</a></li>
                <li>Téléphone : +225 20 25 50 00</li>
            </ul>

            <h2>Article 13 – Modification de la Politique</h2>
            <p>
                Nous pouvons modifier cette politique à tout moment. Les modifications seront publiées
                sur cette page avec une nouvelle date de mise à jour. En cas de modification substantielle,
                nous vous en informerons par email ou notification dans l&apos;application.
            </p>
        </>
    );
}

function PrivacyEN() {
    return (
        <>
            <h1>Privacy Policy</h1>
            <p className="last-updated">Last Updated: February 2026</p>
            <p><em>In case of discrepancy between the French and English versions, the French version shall prevail.</em></p>

            <h2>Article 1 – Data Controller</h2>
            <p>
                The data controller is [COMPANY NAME], a company incorporated under Ivorian law,
                registered with the RCCM under number [RCCM NUMBER], with its registered office
                at [ADDRESS], Abidjan, Ivory Coast.
            </p>
            <p>
                In accordance with Law No. 2013-450 of June 19, 2013 on personal data protection,
                we are committed to protecting your personal information.
            </p>

            <h2>Article 2 – Legal Basis for Processing</h2>
            <p>
                The processing of your personal data is based on your express, free, specific,
                unequivocal, and informed consent, in accordance with Article 23 of Law No. 2013-450.
                This consent is collected when you register for the Service.
            </p>
            <p>We may also process your data based on:</p>
            <ul>
                <li>Performance of a contract to which you are a party</li>
                <li>Compliance with a legal obligation</li>
                <li>Our legitimate interest, when it does not infringe upon your rights</li>
            </ul>

            <h2>Article 3 – Data Collected</h2>
            <p>We collect the following categories of data:</p>

            <h3>3.1 Identification Data</h3>
            <ul>
                <li>First and last name</li>
                <li>Date of birth</li>
                <li>National identification number (NUI, if applicable)</li>
                <li>Identity photograph</li>
            </ul>

            <h3>3.2 Contact Data</h3>
            <ul>
                <li>Mobile phone number</li>
                <li>Email address</li>
                <li>Postal address</li>
                <li>Region of residence</li>
            </ul>

            <h3>3.3 Technical Data</h3>
            <ul>
                <li>IP address</li>
                <li>Device type and operating system</li>
                <li>Login identifiers</li>
                <li>Geolocation data (with your consent)</li>
            </ul>

            <h3>3.4 Usage Data</h3>
            <ul>
                <li>Transaction history</li>
                <li>Service preferences</li>
                <li>Activity logs</li>
            </ul>

            <h2>Article 4 – Processing Purposes</h2>
            <p>Your data is processed for the following purposes:</p>
            <ul>
                <li>Creation and management of your user account</li>
                <li>Provision of micro-insurance services</li>
                <li>Processing payments and transactions</li>
                <li>Management of claims and incidents</li>
                <li>Security and fraud prevention</li>
                <li>Compliance with our legal and regulatory obligations</li>
                <li>Improvement of our services (with anonymization)</li>
                <li>Communication about our services (with your consent)</li>
            </ul>

            <h2>Article 5 – Your Rights (Articles 28-34 of Law 2013-450)</h2>
            <p>In accordance with Ivorian law, you have the following rights:</p>

            <h3>5.1 Right of Access (Article 28)</h3>
            <p>You can obtain confirmation of the processing of your data and receive a copy.</p>

            <h3>5.2 Right of Rectification (Article 29)</h3>
            <p>You can request the correction of inaccurate or incomplete data.</p>

            <h3>5.3 Right of Erasure (Article 30)</h3>
            <p>You can request the deletion of your data in cases provided by law.</p>

            <h3>5.4 Right of Objection (Article 31)</h3>
            <p>You can object to the processing of your data on legitimate grounds.</p>

            <h3>5.5 Right to Portability (Article 32)</h3>
            <p>You can receive your data in a structured format and transmit it to another controller.</p>

            <h3>5.6 Post-Mortem Directives (Article 34)</h3>
            <p>You can define directives concerning the fate of your data after your death.</p>

            <p>To exercise these rights, contact us at [DPO EMAIL].</p>

            <h2>Article 6 – Retention Period</h2>
            <p>Your data is retained in accordance with ARTCI guidelines:</p>
            <ul>
                <li>Account data: duration of contractual relationship + 5 years</li>
                <li>Transaction data: 10 years (accounting and tax obligations)</li>
                <li>Connection data: 1 year</li>
                <li>Marketing data: 3 years after last contact</li>
            </ul>

            <h2>Article 7 – Data Recipients</h2>
            <p>Your data may be shared with:</p>
            <ul>
                <li>Our authorized personnel (strictly necessary)</li>
                <li>Our service providers (payment, hosting, support)</li>
                <li>Judicial or administrative authorities upon legal request</li>
                <li>Our insurance partners for policy execution</li>
            </ul>

            <h2>Article 8 – International Transfers</h2>
            <p>
                Your data is only transferred to third countries if they provide a level of protection
                equivalent to Ivorian law, in accordance with Law No. 2013-450. In the absence of an
                adequacy decision, we implement appropriate safeguards.
            </p>

            <h2>Article 9 – Data Security (Article 19)</h2>
            <p>
                In accordance with Article 19 of Law No. 2013-450, we implement technical and
                organizational measures to protect your data:
            </p>
            <ul>
                <li>Confidentiality: access restricted to authorized personnel</li>
                <li>Integrity: controls to prevent any alteration</li>
                <li>Encryption of network transmissions (HTTPS/TLS)</li>
                <li>Strong authentication and access management</li>
                <li>Regular backups and continuity plans</li>
            </ul>

            <h2>Article 10 – Sensitive Data (Article 7)</h2>
            <p>
                We do not collect sensitive data (ethnic origin, political opinions, religious beliefs,
                health data, sexual orientation) without your express consent and, where applicable,
                prior authorization from ARTCI.
            </p>

            <h2>Article 11 – Cookies and Tracking Technologies</h2>
            <p>We use cookies for:</p>
            <ul>
                <li><strong>Essential cookies:</strong> Service operation (no consent required)</li>
                <li><strong>Analytics cookies:</strong> audience measurement (with your consent)</li>
                <li><strong>Functional cookies:</strong> personalization (with your consent)</li>
            </ul>
            <p>You can manage your preferences through your browser settings.</p>

            <h2>Article 12 – Complaint to ARTCI</h2>
            <p>
                If you believe your rights are not being respected, you can file a complaint with
                the Telecommunications/ICT Regulatory Authority of Ivory Coast (ARTCI):
            </p>
            <ul>
                <li>Website: <a href="https://www.artci.ci" className="text-[#0D9488]">www.artci.ci</a></li>
                <li>Phone: +225 20 25 50 00</li>
            </ul>

            <h2>Article 13 – Policy Modification</h2>
            <p>
                We may modify this policy at any time. Changes will be published on this page with
                a new update date. In case of substantial modification, we will notify you by email
                or notification in the application.
            </p>
        </>
    );
}
