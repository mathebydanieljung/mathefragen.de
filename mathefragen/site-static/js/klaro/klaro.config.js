var klaroConfig = {
    privacyPolicy: '/privacy.html',
    /*
    Bei der Einstellung `true` rendert Klaro die in den Übersetzungen
    `consentModal.description` und `consentNotice.description` angegebenen Texte als
    HTML. So können Sie z.B. eigene Links oder interaktive Inhalte hinzufügen.
    */
    htmlTexts: true,

    /*
    Wenn Sie "acceptAll" auf "true" setzen, wird in der Benachrichtigung und im
    Modal eine Schaltfläche "accept all" angezeigt, die alle Dienste von
    Drittanbietern aktiviert, wenn der Benutzer darauf klickt. Wenn auf "false"
    gesetzt, wird eine Schaltfläche "accept" angezeigt, die nur die Dienste
    aktiviert, die im Zustimmungsmodus aktiviert sind.
    */
    acceptAll: true,

    mustConsent: false,

    services: [
        {
            name: "login",
            title: "Login",
            purposes: ["essential"],
            required: true,
            optOut: false,
            description: "Der Login ist notwendig, um mit der Seite interagieren zu können..",
        },
        {
            name: 'youtube',
            contextualConsentOnly: true,
            purposes: ['essential'],
            description: "YouTube-Videos, die zum weiteren Verständnis der Inhalte beitragen.",
        },
        {
            name: 'mathjax',
            required: true,
            purposes: ['essential'],
            description: "Mathjax wird benötigt, um mathematische Formeln darzustellen.",
        },
        {
            name: 'tinymce',
            required: true,
            purposes: ['essential'],
            description: "TinyMCE wird benötigt, um Texte zu formatieren.",
        },
        {
            name: 'cloudflare-turnstile',
            required: true,
            purposes: ['essential'],
            description: "Cloudflare schützt die Seite vor Angriffen.",
        },
        {
            // In GTM, you should define a custom event trigger named `klaro-google-analytics-accepted` which should trigger the Google Analytics integration.
            name: 'google-analytics',
            cookies: [
                /^_ga(_.*)?/ // we delete the Google Analytics cookies if the user declines its use
            ],
            purposes: ['analytics'],
        },
    ],
    translations: {
        zz: {
            privacyPolicyUrl: '/privacy',

        },
        de: {
            /*
            You can specify a language-specific link to your privacy policy here.
            */
            privacyPolicyUrl: '/datenschutz',
            consentNotice: {
                description: '🍪 Wir verwenden Cookies.<br/>Lerne mehr darüber, wie wir Cookies verwenden und wie du deine Einstellungen anpassen kannst.',
            },
            consentModal: {
                description:
                    'Hier kannst du sehen und anpassen, welche Informationen wir über dich sammeln.'
            },
            /*
            You should also define translations for every purpose you define in the
            'services' section. You can define a title and an (optional) description.
            */
            purposes: {
                analytics: {
                    title: 'Besucher-Statistiken'
                },
                essential: {
                    title: 'Essenziell'
                },
                security: {
                    title: 'Sicherheit'
                },
                livechat: {
                    title: 'Live Chat'
                },
                advertising: {
                    title: 'Anzeigen von Werbung'
                },
                styling: {
                    title: 'Styling'
                },
            },
        },
        en: {
            privacyPolicyUrl: '/privacy',
            consentNotice: {
                description: '🍪 We use cookies.<br/>Learn more about how we use cookies and how you can customize your settings.',
            },
            consentModal: {
                description:
                    'Here you can see and customize the information that we collect about you.',
            },
            purposes: {
                analytics: {
                    title: 'Analytics'
                },
                essential: {
                    title: 'Essential'
                },
                security: {
                    title: 'Security'
                },
                livechat: {
                    title: 'Livechat'
                },
                advertising: {
                    title: 'Advertising'
                },
                styling: {
                    title: 'Styling'
                },
            },
        },
    },
};