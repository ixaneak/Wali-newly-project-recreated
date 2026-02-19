import { createWaliChat, getQuickResponse } from '@/lib/ai/wali-service';

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();
    
    // Check for quick responses first
    const lastMessage = messages[messages.length - 1]?.content;
    const quickResponse = lastMessage ? getQuickResponse(lastMessage) : null;
    
    if (quickResponse) {
      return new Response(
        JSON.stringify({ content: quickResponse, role: 'assistant' }),
        { headers: { 'Content-Type': 'application/json' } }
      );
    }
    
    // Create chat response from AI
    const result = await createWaliChat(messages);
    
    return new Response(
      JSON.stringify(result),
      { headers: { 'Content-Type': 'application/json' } }
    );
    
  } catch (error) {
    console.error('Chat API error:', error);
    return new Response(
      JSON.stringify({ 
        content: 'Désolé, je rencontre un problème technique. Réessaie dans quelques instants.',
        role: 'assistant'
      }),
      { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}
