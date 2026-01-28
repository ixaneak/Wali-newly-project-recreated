import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number): string {
    return `${amount.toLocaleString('fr-FR')} XOF`;
}

export function formatPhone(phone: string): string {
    // Format +225XXXXXXXXXX to +225 XX XX XX XX XX
    if (phone.startsWith('+225')) {
        const digits = phone.substring(4);
        return `+225 ${digits.match(/.{1,2}/g)?.join(' ') || digits}`;
    }
    return phone;
}

export function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: 'long',
        year: 'numeric',
    });
}

export function formatDateTime(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString('fr-FR', {
        day: '2-digit',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}
