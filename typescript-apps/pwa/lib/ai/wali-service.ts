/**
 * WALI AI CONCIERGE SERVICE
 * 
 * Natural language insurance assistant for Côte d'Ivoire's informal sector.
 * Speaks French and local languages (Dioula, Baoulé context).
 * Understands informal sector challenges and provides culturally appropriate advice.
 */

import OpenAI from 'openai';
import { 
  MOCK_PHARMACIES, 
  MOCK_FORMULARY, 
  findMockDrug 
} from '@/lib/mocks/pharmacy-mocks';

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || '',
});

// Wali's personality and context
export const WALI_SYSTEM_PROMPT = `Tu es Wali, le concierge IA de micro-assurance pour les artisans et travailleurs du secteur informel de Côte d'Ivoire.

TON RÔLE:
- Aider les utilisateurs à comprendre leur assurance santé et équipement
- Répondre aux questions sur les pharmacies partenaires
- Expliquer les procédures de remboursement
- Donner des conseils de prévention santé adaptés au contexte ivoirien

TON STYLE:
- Parle en français simple et chaleureux
- Sois patient et pédagogue
- Utilise des expressions locales appropriées quand c'est naturel
- Montre de l'empathie pour les difficultés des artisans
- Sois concis mais complet

CONTEXTE CULTUREL:
- Les utilisateurs sont souvent des artisans (coiffeurs, mécaniciens, vendeurs, etc.)
- Ils peuvent ne pas être familiers avec les termes d'assurance
- La confiance est importante - sois transparent sur ce qui est couvert ou non
- Mentionne les pharmacies partenaires quand c'est pertinent

RÈGLES IMPORTANTES:
- Ne donne JAMAIS de conseils médicaux diagnostics (toujours renvoyer vers un médecin)
- Ne promets pas de remboursements que tu ne peux pas garantir
- Sois honnête sur les limites de couverture
- Si tu ne sais pas, dis-le clairement`;

// Tool definitions for function calling
const TOOLS = [
  {
    type: "function" as const,
    function: {
      name: "findPharmacies",
      description: "Trouver les pharmacies partenaires Wali près d'une ville",
      parameters: {
        type: "object" as const,
        properties: {
          city: { type: "string", description: "Ville en Côte d'Ivoire (ex: Abidjan, Bouaké, San Pedro)" }
        },
        required: ["city"]
      }
    }
  },
  {
    type: "function" as const,
    function: {
      name: "searchMedicine",
      description: "Rechercher un médicament dans le formulaire Wali",
      parameters: {
        type: "object" as const,
        properties: {
          name: { type: "string", description: "Nom du médicament ou molécule" }
        },
        required: ["name"]
      }
    }
  },
  {
    type: "function" as const,
    function: {
      name: "checkCoverage",
      description: "Vérifier la couverture d'un médicament spécifique",
      parameters: {
        type: "object" as const,
        properties: {
          medicineCode: { type: "string", description: "Code du médicament (ex: MED-PARA-500)" },
          quantity: { type: "number", default: 1, description: "Quantité souhaitée" }
        },
        required: ["medicineCode"]
      }
    }
  },
  {
    type: "function" as const,
    function: {
      name: "getReimbursementInfo",
      description: "Obtenir des informations sur les remboursements",
      parameters: {
        type: "object" as const,
        properties: {
          type: { 
            type: "string", 
            enum: ["pharmacy", "hospital", "consultation"],
            description: "Type de frais" 
          }
        },
        required: ["type"]
      }
    }
  },
  {
    type: "function" as const,
    function: {
      name: "getHealthTips",
      description: "Conseils santé pour artisans et travailleurs informels",
      parameters: {
        type: "object" as const,
        properties: {
          category: { 
            type: "string",
            enum: ["general", "back_pain", "eye_strain", "dust_exposure", "stress"],
            description: "Catégorie de conseil" 
          }
        },
        required: ["category"]
      }
    }
  }
];

// Tool implementations
async function executeTool(name: string, args: any) {
  switch (name) {
    case 'findPharmacies': {
      const { city } = args;
      const pharmacies = MOCK_PHARMACIES.filter(p => 
        p.city?.toLowerCase().includes(city.toLowerCase())
      );
      
      if (pharmacies.length === 0) {
        return {
          found: false,
          message: `Je n'ai trouvé aucune pharmacie partenaire à ${city}. Les villes avec pharmacies: Abidjan, Bouaké, San Pedro.`,
          pharmacies: []
        };
      }
      
      return {
        found: true,
        message: `J'ai trouvé ${pharmacies.length} pharmacie(s) à ${city}`,
        pharmacies: pharmacies.map(p => ({
          name: p.name,
          address: p.address,
          phone: p.phone,
          status: p.subscription_status,
          city: p.city
        }))
      };
    }
    
    case 'searchMedicine': {
      const { name } = args;
      const drugs = MOCK_FORMULARY.filter(d => 
        d.name.toLowerCase().includes(name.toLowerCase()) ||
        d.generic_name.toLowerCase().includes(name.toLowerCase()) ||
        d.code.toLowerCase().includes(name.toLowerCase())
      );
      
      if (drugs.length === 0) {
        return {
          found: false,
          message: `Je n'ai pas trouvé "${name}" dans notre formulaire. Essaie avec le nom générique (par exemple "Paracétamol" au lieu de "Doliprane").`
        };
      }
      
      return {
        found: true,
        message: `J'ai trouvé ${drugs.length} médicament(s)`,
        drugs: drugs.map(d => ({
          name: d.name,
          generic: d.generic_name,
          coverage: d.coverage_percentage,
          price: d.unit_price,
          status: d.status,
          inStock: d.in_stock,
          prescription: d.requires_prescription ? 'Oui' : 'Non'
        }))
      };
    }
    
    case 'checkCoverage': {
      const { medicineCode, quantity = 1 } = args;
      const drug = findMockDrug(medicineCode);
      
      if (!drug) {
        return {
          covered: false,
          message: `Médicament non trouvé dans notre formulaire.`,
          alternatives: []
        };
      }
      
      const totalPrice = drug.unit_price * quantity;
      const waliCovers = Math.round(totalPrice * (drug.coverage_percentage / 100));
      const patientPays = totalPrice - waliCovers;
      
      return {
        covered: drug.status === 'covered',
        message: `${drug.name}: ${drug.coverage_percentage}% couvert`,
        details: {
          name: drug.name,
          quantity: quantity,
          totalPrice: `${totalPrice} FCFA`,
          waliCovers: `${waliCovers} FCFA`,
          patientPays: `${patientPays} FCFA`,
          requiresPrescription: drug.requires_prescription,
          inStock: drug.in_stock
        }
      };
    }
    
    case 'getReimbursementInfo': {
      const { type } = args;
      const info: Record<string, any> = {
        pharmacy: {
          coverage: '80-95% selon le médicament',
          process: 'Présente ta carte Wali en pharmacie partenaire. Le remboursement est automatique.',
          delay: 'Immédiat en pharmacie partenaire',
          documents: 'Carte Wali ou QR Code suffisent'
        },
        hospital: {
          coverage: 'Jusqu\'à 500,000 FCFA/an pour hospitalisation',
          process: 'Préviens Wali sous 48h pour une hospitalisation. Garde tous les reçus.',
          delay: '5-10 jours ouvrés après envoi des documents',
          documents: 'Factures, ordonnances, compte-rendu médical'
        },
        consultation: {
          coverage: '80% des frais de consultation',
          process: 'Paie d\'abord, puis demande le remboursement via l\'app.',
          delay: '3-5 jours ouvrés',
          documents: 'Reçu de paiement, ordonnance si médicaments'
        }
      };
      
      return info[type];
    }
    
    case 'getHealthTips': {
      const { category } = args;
      const tips: Record<string, any> = {
        general: [
          'Bois au moins 1.5L d\'eau par jour, surtout sous le soleil ivoirien',
          'Fais une pause de 10 minutes toutes les 2 heures de travail',
          'Lave-toi les mains régulièrement, surtout avant de manger'
        ],
        back_pain: [
          'Si tu es coiffeur ou mécanicien, change souvent de position',
          'Fais des étirements le matin avant de commencer ta journée',
          'Dors sur un matelas de bonne qualité - c\'est un investissement santé'
        ],
        eye_strain: [
          'Pour les couturiers et soudeurs: protège tes yeux avec des lunettes adaptées',
          'Regarde au loin toutes les 20 minutes si tu travailles sur écran',
          'L\'éclairage de ton atelier doit être suffisant'
        ],
        dust_exposure: [
          'Les menuisiers et maçons: porte un masque quand tu travaille la poussière',
          'Aère bien ton espace de travail',
          'Lave-toi le visage et les mains à la fin de chaque journée'
        ],
        stress: [
          'Parle de tes soucis - le stress des artisans est réel',
          'Prends du temps pour toi, même 30 minutes par jour',
          'Une bonne nuit de sommeil fait toute la différence'
        ]
      };
      
      return {
        category: category,
        tips: tips[category],
        message: `Conseils pour ${category.replace('_', ' ')}:`
      };
    }
    
    default:
      return { error: 'Tool not found' };
  }
}

// Main chat function
export async function createWaliChat(messages: any[]) {
  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: WALI_SYSTEM_PROMPT },
        ...messages
      ],
      tools: TOOLS,
      tool_choice: 'auto',
      temperature: 0.7,
    });

    const message = response.choices[0].message;

    // If there are tool calls, execute them and get final response
    if (message.tool_calls && message.tool_calls.length > 0) {
      const toolResults = [];
      
      for (const toolCall of message.tool_calls) {
        // Type guard for function tool calls
        if ('function' in toolCall) {
          const result = await executeTool(
            toolCall.function.name,
            JSON.parse(toolCall.function.arguments)
          );
          toolResults.push({
            tool_call_id: toolCall.id,
            role: 'tool' as const,
            content: JSON.stringify(result)
          });
        }
      }

      // Get final response with tool results
      const finalResponse = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: WALI_SYSTEM_PROMPT },
          ...messages,
          message,
          ...toolResults
        ],
        temperature: 0.7,
      });

      return {
        content: finalResponse.choices[0].message.content,
        role: 'assistant'
      };
    }

    return {
      content: message.content,
      role: 'assistant'
    };

  } catch (error) {
    console.error('OpenAI API error:', error);
    throw error;
  }
}

// Quick responses for common questions (fallback)
export const QUICK_RESPONSES: Record<string, string> = {
  'bonjour': 'Bonjour! Je suis Wali, ton assistant assurance. Comment puis-je t\'aider aujourd\'hui?',
  'salut': 'Salut! Prêt à répondre à tes questions sur ton assurance Wali.',
  'qui es-tu': 'Je suis Wali, le concierge IA de IvoireShield. Je t\'aide à comprendre ton assurance et à trouver des pharmacies partenaires.',
  'merci': 'Avec plaisir! N\'hésite pas si tu as d\'autres questions. Je suis là pour t\'aider.',
  'au revoir': 'Au revoir! Prends soin de toi. N\'oublie pas: ta santé est ton capital le plus précieux.',
};

export function getQuickResponse(message: string): string | null {
  const normalized = message.toLowerCase().trim();
  return QUICK_RESPONSES[normalized] || null;
}
