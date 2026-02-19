'use client';

import { useState } from 'react';
import { Globe, Check } from 'lucide-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

import { useLanguage } from '@/components/LanguageProvider';
import { Language } from '@/lib/translations';

const languages = [
    { code: 'fr', name: 'Français', flag: '🇨🇮' },
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'ba', name: 'Baoulé', flag: '🇨🇮' },
    { code: 'di', name: 'Dioula', flag: '🇨🇮' },
];

export function LanguageSwitcher() {
    const { language, setLanguage } = useLanguage();

    return (
        <div className="absolute top-4 right-4 z-50">
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="text-white/80 hover:text-white hover:bg-white/10 gap-2 rounded-full px-3"
                    >
                        <Globe className="w-4 h-4" />
                        <span className="uppercase">{language}</span>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-[150px] bg-black/90 backdrop-blur-md border border-white/10 text-white">
                    {languages.map((lang) => (
                        <DropdownMenuItem
                            key={lang.code}
                            className="group flex items-center justify-between cursor-pointer hover:bg-emerald-500/20 focus:bg-emerald-500/20 focus:text-emerald-400"
                            onClick={() => setLanguage(lang.code as Language)}
                        >
                            <div className="flex items-center gap-2">
                                <span>{lang.flag}</span>
                                <span className="text-sm font-medium">{lang.name}</span>
                            </div>
                            {language === lang.code && (
                                <Check className="w-3 h-3 text-emerald-400" />
                            )}
                        </DropdownMenuItem>
                    ))}
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    );
}

export default LanguageSwitcher;
