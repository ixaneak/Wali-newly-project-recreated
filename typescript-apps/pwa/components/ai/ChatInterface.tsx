'use client';

import { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  Sparkles,
  MapPin,
  Pill,
  ShieldCheck,
  Heart,
  ChevronRight,
  X
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface ChatInterfaceProps {
  className?: string;
  embedded?: boolean;
}

const SUGGESTED_QUESTIONS = [
  { icon: MapPin, text: 'Pharmacies près de moi', color: 'text-emerald-500' },
  { icon: Pill, text: 'Est-ce que le Doliprane est couvert?', color: 'text-blue-500' },
  { icon: ShieldCheck, text: 'Comment faire rembourser une consultation?', color: 'text-violet-500' },
  { icon: Heart, text: 'Conseils santé pour artisans', color: 'text-rose-500' },
];

export default function ChatInterface({ className, embedded = false }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Bonjour! Je suis Wali, ton assistant assurance. Je peux t\'aider à trouver des pharmacies, vérifier la couverture de tes médicaments, ou répondre à tes questions sur ton assurance. Comment puis-je t\'aider aujourd\'hui?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Hide suggestions after first message
  useEffect(() => {
    if (messages.length > 1) {
      setShowSuggestions(false);
    }
  }, [messages.length]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [...messages, userMessage] })
      });

      const data = await response.json();

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.content
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Désolé, je rencontre un problème technique. Réessaie dans quelques instants.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (text: string) => {
    setInput(text);
    // Auto-submit after a brief delay
    setTimeout(() => {
      const form = document.getElementById('chat-form') as HTMLFormElement;
      form?.requestSubmit();
    }, 100);
  };

  return (
    <div className={cn(
      "flex flex-col bg-slate-950",
      embedded ? "h-full" : "h-screen",
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-emerald-500" />
          </div>
          <div>
            <h1 className="font-bold text-white">Wali</h1>
            <p className="text-xs text-slate-400">Ton concierge IA assurance</p>
          </div>
        </div>
        
        {embedded && (
          <button className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex gap-3",
              message.role === 'user' ? "flex-row-reverse" : ""
            )}
          >
            {/* Avatar */}
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
              message.role === 'assistant' 
                ? "bg-emerald-500/10 border border-emerald-500/20" 
                : "bg-slate-700"
            )}>
              {message.role === 'assistant' ? (
                <Bot className="w-4 h-4 text-emerald-500" />
              ) : (
                <User className="w-4 h-4 text-slate-300" />
              )}
            </div>

            {/* Message Bubble */}
            <div className={cn(
              "max-w-[80%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap",
              message.role === 'assistant'
                ? "bg-slate-800/50 border border-slate-700 text-slate-200"
                : "bg-emerald-600 text-white"
            )}>
              {message.content}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Bot className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl px-4 py-3 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-emerald-500" />
              <span className="text-sm text-slate-400">Wali réfléchit...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {showSuggestions && messages.length === 1 && (
        <div className="px-4 pb-4">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Questions suggérées</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {SUGGESTED_QUESTIONS.map((q, i) => (
              <button
                key={i}
                onClick={() => handleSuggestionClick(q.text)}
                className="flex items-center gap-3 p-3 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 rounded-xl transition text-left group"
              >
                <q.icon className={cn("w-4 h-4", q.color)} />
                <span className="text-sm text-slate-300 group-hover:text-white flex-1">
                  {q.text}
                </span>
                <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/50">
        <form id="chat-form" onSubmit={handleSubmit} className="flex gap-2">
          <div className="flex-1 relative">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Écris ton message..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-4 pr-12 py-3 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/50"
              disabled={isLoading}
            />
          </div>
          <Button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed px-4"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </form>
        <p className="text-[10px] text-slate-600 text-center mt-2">
          Wali peut faire des erreurs. Vérifie les informations importantes.
        </p>
      </div>
    </div>
  );
}
