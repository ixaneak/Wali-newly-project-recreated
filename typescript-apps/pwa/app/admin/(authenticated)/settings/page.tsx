"use client";

import React, { useState } from 'react';
import {
    Settings,
    User,
    Bell,
    Shield,
    Globe,
    Lock,
    CreditCard,
    Save,
    CheckCircle2,
    Database,
    Zap,
    Scale,
    Cpu,
    Smartphone
} from 'lucide-react';
import AdminHeader from '@/components/admin/AdminHeader';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';

export default function AdminSettingsPage() {
    const [saving, setSaving] = useState(false);

    const handleSave = () => {
        setSaving(true);
        setTimeout(() => {
            setSaving(false);
            toast.success("Configurations enregistrées avec succès");
        }, 1200);
    };

    return (
        <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
            <AdminHeader
                title="Configuration Système"
                description="Paramètres globaux, conformité et sécurité Wali"
            />

            <Tabs defaultValue="general" className="w-full">
                <div className="grid grid-cols-1 xl:grid-cols-4 gap-10">
                    {/* Navigation Sidebar */}
                    <aside className="space-y-6">
                        <TabsList className="flex flex-col h-auto bg-slate-900/40 p-2 rounded-[2rem] border border-slate-800 space-y-2">
                            {[
                                { id: 'general', label: 'Général', icon: Globe },
                                { id: 'profile', label: 'Profil Admin', icon: User },
                                { id: 'security', label: 'Sécurité API', icon: Shield },
                                { id: 'notifications', label: 'Notifications', icon: Bell },
                                { id: 'gateways', label: 'Passerelles', icon: Smartphone },
                            ].map((item) => (
                                <TabsTrigger
                                    key={item.id}
                                    value={item.id}
                                    className="w-full justify-start px-6 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest gap-4 data-[state=active]:bg-cyan-500 data-[state=active]:text-white text-slate-500 hover:text-slate-300 transition-all"
                                >
                                    <item.icon size={18} />
                                    {item.label}
                                </TabsTrigger>
                            ))}
                        </TabsList>

                        <Card className="border-slate-800 bg-slate-900/40 p-8 rounded-[2rem]">
                            <div className="flex items-center gap-3 mb-4">
                                <Cpu className="text-cyan-500" size={18} />
                                <span className="text-[10px] font-black text-white uppercase tracking-widest">Version Infrastructure</span>
                            </div>
                            <p className="text-[10px] text-slate-500 font-bold mb-6">Wali-Console-Stable 1.4.0b</p>
                            <Button variant="outline" className="w-full h-10 border-slate-800 text-[9px] font-black tracking-widest bg-slate-950/50">VÉRIFIER MAJ</Button>
                        </Card>
                    </aside>

                    {/* Content Area */}
                    <div className="xl:col-span-3">
                        <TabsContent value="general" className="mt-0 space-y-10">
                            <Card className="border-slate-800 bg-slate-900/40 rounded-[2.5rem]">
                                <CardHeader className="p-10 border-b border-slate-800">
                                    <CardTitle className="uppercase tracking-tight">Configuration de Base</CardTitle>
                                    <CardDescription>Paramètres de localisation et identité visuelle</CardDescription>
                                </CardHeader>
                                <CardContent className="p-10 space-y-10">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                                        <div className="space-y-4">
                                            <Label>Nom de la Plateforme</Label>
                                            <Input defaultValue="Wali Admin Console" className="bg-slate-950/50" />
                                        </div>
                                        <div className="space-y-4">
                                            <Label>Devise Primaire</Label>
                                            <Input defaultValue="XOF (FCFA)" className="bg-slate-950/50" />
                                        </div>
                                    </div>

                                    <div className="pt-6 border-t border-slate-800/50 flex items-center justify-between">
                                        <div>
                                            <p className="text-sm font-bold text-white">Mode Maintenance</p>
                                            <p className="text-xs text-slate-500">Désactiver l'accès artisan temporairement</p>
                                        </div>
                                        <Switch />
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="border-slate-800 bg-slate-900/40 rounded-[2.5rem]">
                                <CardHeader className="p-10 border-b border-slate-800">
                                    <CardTitle className="uppercase tracking-tight">Compliance Settings</CardTitle>
                                </CardHeader>
                                <CardContent className="p-10">
                                    <div className="space-y-4">
                                        <Label>Identifiant COSUMAF Géré</Label>
                                        <Input defaultValue="WALI-CI-2024-EX" className="bg-slate-950/50" />
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        <TabsContent value="security" className="mt-0 space-y-10">
                            <Card className="border-slate-800 bg-slate-900/40 rounded-[2.5rem]">
                                <CardHeader className="p-10 border-b border-slate-800">
                                    <CardTitle className="uppercase tracking-tight">Protocoles de Sécurité</CardTitle>
                                </CardHeader>
                                <CardContent className="p-10 space-y-10">
                                    <div className="flex items-center justify-between p-8 rounded-3xl bg-slate-950/40 border border-slate-800">
                                        <div>
                                            <p className="text-sm font-bold text-white uppercase tracking-tight">Authentification à Deux Facteurs (2FA)</p>
                                            <p className="text-xs text-slate-500 mt-1">Requise pour toutes les approbations de claims de &gt; 100k FCFA</p>
                                        </div>
                                        <Switch defaultChecked />
                                    </div>

                                    <div className="space-y-4">
                                        <Label>Secret de Signature API (mTLS)</Label>
                                        <div className="relative group">
                                            <Input type="password" value="secret_sig_wali_prod_88291..." readOnly className="bg-slate-950/50 pr-24" />
                                            <Button variant="ghost" className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-black text-cyan-500">RÉVÉLER</Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </div>
                </div>

                {/* Footer Save Button */}
                <div className="fixed bottom-10 right-10 flex gap-4 animate-in slide-in-from-right-10">
                    <Button variant="cyan" onClick={handleSave} disabled={saving} className="h-14 px-10 font-black uppercase tracking-widest text-[10px] shadow-2xl shadow-cyan-500/20">
                        {saving ? "SYNCHRONISATION..." : "ENREGISTRER LA CONFIGURATION"}
                    </Button>
                </div>
            </Tabs>
        </div>
    );
}
