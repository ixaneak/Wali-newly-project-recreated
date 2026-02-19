import { Metadata } from 'next';
import ChatInterface from '@/components/ai/ChatInterface';

export const metadata: Metadata = {
  title: 'Wali - Ton Concierge IA',
  description: 'Discute avec Wali, ton assistant IA pour toutes tes questions assurance santé en Côte d\'Ivoire.',
};

export default function ConciergePage() {
  return (
    <main className="h-screen">
      <ChatInterface />
    </main>
  );
}
