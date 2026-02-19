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
    Smartphone,
    Mail,
    MessageSquare,
    Webhook,
    Key,
    RefreshCw,
    ToggleLeft,
    ToggleRight
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
    const [activeTab, setActiveTab] = useState('general');

    const handleSave = () => {
        setSaving(true);
        setTimeout(() => {
            setSaving(false);
            toast.success("Configurations enregistrées avec succès");
        }, 1200);
    };

    const tabItems = [
        { id: 'general', label: 'Général', icon: Globe },
        { id: 'profile', label: 'Profil Admin', icon: User },
        { id: 'security', label: 'Sécurité API', icon: Shield },
        { id: 'notifications', label: 'Notifications', icon: Bell },
        { id: 'gateways', label: 'Passerelles', icon: Smartphone },
    ];

    return (
        <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
            <AdminHeader
                title="Configuration Système"
                description="Paramètres globaux, conformité et sécurité Wali"
            />

            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <div className="grid grid-cols-1 xl:grid-cols-4 gap-10">
                    {/* Navigation Sidebar */}
                    <aside className="space-y-6">
                        <TabsList className="flex flex-col h-auto bg-slate-900/40 p-2 rounded-2xl border border-slate-800 space-y-2">
                            {tabItems.map((item) => (
                                <TabsTrigger
                                    key={item.id}
                                    value={item.id}
                                    className="w-full justify-start px-6 py-4 rounded-xl font-black text-[10px] uppercase tracking-widest gap-4 data-[state=active]:bg-cyan-500 data-[state=active]:text-white text-slate-500 hover:text-slate-300 transition-all"
                                >
                                    <item.icon size={18} />
                                    {item.label}
                                </TabsTrigger>
                            ))}
                        </TabsList>

                        <Card className="border-slate-800 bg-slate-900/40 p-6 rounded-2xl">
                            <div className="flex items-center gap-3 mb-4">
                                <Cpu className="text-cyan-500" size={18} />
                                <span className="text-[10px] font-black text-white uppercase tracking-widest">Version Infrastructure</span>
                            </div>
                            <p className="text-[10px] text-slate-500 font-bold mb-6">Wali-Console-Stable 1.4.0b</p>
                            <Button variant="outline" className="w-full h-10 border-slate-800 text-[9px] font-black tracking-widest bg-slate-950/50 hover:bg-slate-800">
                                VÉRIFIER MAJ
                            </Button>
                        </Card>
                    </aside>

                    {/* Content Area */}
                    <div className="xl:col-span-3 space-y-6">
                        {/* GENERAL TAB */}
                        <TabsContent value="general" className="mt-0 space-y-6">
                            <Card className="border-slate-800 bg-slate-900/40 rounded-2xl">
                                <CardHeader className="p-8 border-b border-slate-800">
                                    <CardTitle className="text-sm uppercase tracking-widest font-black">Configuration de Base</CardTitle>
                                    <CardDescription>Paramètres de localisation et identité visuelle</CardDescription>
                                </CardHeader>
                                <CardContent className="p-8 space-y-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="space-y-3">
                                            <Label className="text-xs font-bold uppercase tracking-wider">Nom de la Plateforme</Label>
                                            <Input defaultValue="Wali Admin Console" className="bg-slate-950/50 border-slate-800" />
                                        </div>
                                        <div className="space-y-3">
                                            <Label className="text-xs font-bold uppercase tracking-wider">Devise Primaire</Label>
                                            <select defaultValue="xof" className="w-full h-10 px-3 rounded-md bg-slate-950/50 border border-slate-800 text-white text-sm">
                                                <option value="xof">XOF (FCFA)</option>
                                                <option value="usd">USD ($)</option>
                                                <option value="eur">EUR (€)</option>
                                            </select>
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

                            <Card className="border-slate-800 bg-slate-900/40 rounded-2xl">
                                <CardHeader className="p-8 border-b border-slate-800">
                                    <CardTitle className="text-sm uppercase tracking-widest font-black">Compliance Settings</CardTitle>
                                </CardHeader>
                                <CardContent className="p-8 space-y-6">
                                    <div className="space-y-3">
                                        <Label className="text-xs font-bold uppercase tracking-wider">Identifiant COSUMAF</Label>
                                        <Input defaultValue="WALI-CI-2024-EX" className="bg-slate-950/50 border-slate-800 font-mono" />
                                    </div>
                                    <div className="space-y-3">
                                        <Label className="text-xs font-bold uppercase tracking-wider">Période de Rétention (jours)</Label>
                                        <Input type="number" defaultValue="1825" className="bg-slate-950/50 border-slate-800" />
                                        <p className="text-[10px] text-slate-500">5 ans minimum requis par CIMA (1825 jours)</p>
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        {/* PROFILE TAB */}
                        <TabsContent value="profile" className="mt-0 space-y-6">
                            <Card className="border-slate-800 bg-slate-900/40 rounded-2xl">
                                <CardHeader className="p-8 border-b border-slate-800">
                                    <CardTitle className="text-sm uppercase tracking-widest font-black">Profil Administrateur</CardTitle>
                                    <CardDescription>Informations personnelles et préférences</CardDescription>
                                </CardHeader>
                                <CardContent className="p-8 space-y-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="space-y-3">
                                            <Label className="text-xs font-bold uppercase tracking-wider">Nom complet</Label>
                                            <Input defaultValue="Admin Wali" className="bg-slate-950/50 border-slate-800" />
                                        </div>
                                        <div className="space-y-3">
                                            <Label className="text-xs font-bold uppercase tracking-wider">Email</Label>
                                            <Input type="email" defaultValue="admin@wali.ci" className="bg-slate-950/50 border-slate-800" />
                                        </div>
                                    </div>
                                    <div className="space-y-3">
                                        <Label className="text-xs font-bold uppercase tracking-wider">Téléphone</Label>
                                        <Input defaultValue="+225 07 07 07 07 07" className="bg-slate-950/50 border-slate-800" />
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="border-slate-800 bg-slate-900/40 rounded-2xl">
                                <CardHeader className="p-8 border-b border-slate-800">
                                    <CardTitle className="text-sm uppercase tracking-widest font-black">Changer le mot de passe</CardTitle>
                                </CardHeader>
                                <CardContent className="p-8 space-y-6">
                                    <div className="space-y-3">
                                        <Label className="text-xs font-bold uppercase tracking-wider">Mot de passe actuel</Label>
                                        <Input type="password" placeholder="••••••••" className="bg-slate-950/50 border-slate-800" />
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="space-y-3">
                                            <Label className="text-xs font-bold uppercase tracking-wider">Nouveau mot de passe</Label>
                                            <Input type="password" placeholder="••••••••" className="bg-slate-950/50 border-slate-800" />
                                        </div>
                                        <div className="space-y-3">
                                            <Label className="text-xs font-bold uppercase tracking-wider">Confirmer le mot de passe</Label>
                                            <Input type="password" placeholder="••••••••" className="bg-slate-950/50 border-slate-800" />
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        {/* SECURITY TAB */}
                        <TabsContent value="security" className="mt-0 space-y-6">
                            <Card className="border-slate-800 bg-slate-900/40 rounded-2xl">
                                <CardHeader className="p-8 border-b border-slate-800">
                                    <CardTitle className="text-sm uppercase tracking-widest font-black">Protocoles de Sécurité</CardTitle>
                                </CardHeader>
                                <CardContent className="p-8 space-y-6">
                                    <div className="flex items-center justify-between p-6 rounded-xl bg-slate-950/40 border border-slate-800">
                                        <div>
                                            <p className="text-sm font-bold text-white">Authentification à Deux Facteurs (2FA)</p>
                                            <p className="text-xs text-slate-500 mt-1">Requise pour les approbations de claims &gt; 100k FCFA</p>
                                        </div>
                                        <Switch defaultChecked />
                                    </div>

                                    <div className="flex items-center justify-between p-6 rounded-xl bg-slate-950/40 border border-slate-800">
                                        <div>
                                            <p className="text-sm font-bold text-white">Verrouillage session inactive</p>
                                            <p className="text-xs text-slate-500 mt-1">Déconnexion automatique après 15 minutes d'inactivité</p>
                                        </div>
                                        <Switch defaultChecked />
                                    </div>

                                    <div className="space-y-3 pt-4">
                                        <Label className="text-xs font-bold uppercase tracking-wider">Secret de Signature API (mTLS)</Label>
                                        <div className="relative group">
                                            <Input type="password" value="secret_sig_wali_prod_88291..." readOnly className="bg-slate-950/50 border-slate-800 pr-24 font-mono text-xs" />
                                            <Button variant="ghost" className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-black text-cyan-500 hover:text-cyan-400">
                                                RÉVÉLER
                                            </Button>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        <Label className="text-xs font-bold uppercase tracking-wider">Clé API Webhook</Label>
                                        <div className="flex gap-3">
                                            <Input value="whk_live_xxxxxxxxxxxxxxxx" readOnly className="bg-slate-950/50 border-slate-800 font-mono text-xs" />
                                            <Button variant="outline" className="border-slate-800 text-[10px] font-black tracking-wider">
                                                <RefreshCw size={14} className="mr-2" />
                                                RÉGÉNÉRER
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        {/* NOTIFICATIONS TAB */}
                        <TabsContent value="notifications" className="mt-0 space-y-6">
                            <Card className="border-slate-800 bg-slate-900/40 rounded-2xl">
                                <CardHeader className="p-8 border-b border-slate-800">
                                    <CardTitle className="text-sm uppercase tracking-widest font-black">Canaux de Notification</CardTitle>
                                    <CardDescription>Configurer les alertes et notifications système</CardDescription>
                                </CardHeader>
                                <CardContent className="p-8 space-y-6">
                                    <div className="flex items-center justify-between p-6 rounded-xl bg-slate-950/40 border border-slate-800">
                                        <div className="flex items-center gap-4">
                                            <Mail className="text-slate-500" size={20} />
                                            <div>
                                                <p className="text-sm font-bold text-white">Notifications Email</p>
                                                <p className="text-xs text-slate-500">Alertes pour nouveaux claims et incidents critiques</p>
                                            </div>
                                        </div>
                                        <Switch defaultChecked />
                                    </div>

                                    <div className="flex items-center justify-between p-6 rounded-xl bg-slate-950/40 border border-slate-800">
                                        <div className="flex items-center gap-4">
                                            <MessageSquare className="text-slate-500" size={20} />
                                            <div>
                                                <p className="text-sm font-bold text-white">Notifications WhatsApp</p>
                                                <p className="text-xs text-slate-500">Alertes urgentes pour l'équipe admin</p>
                                            </div>
                                        </div>
                                        <Switch />
                                    </div>

                                    <div className="flex items-center justify-between p-6 rounded-xl bg-slate-950/40 border border-slate-800">
                                        <div className="flex items-center gap-4">
                                            <Webhook className="text-slate-500" size={20} />
                                            <div>
                                                <p className="text-sm font-bold text-white">Webhooks</p>
                                                <p className="text-xs text-slate-500">Notifications push vers systèmes externes</p>
                                            </div>
                                        </div>
                                        <Switch defaultChecked />
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="border-slate-800 bg-slate-900/40 rounded-2xl">
                                <CardHeader className="p-8 border-b border-slate-800">
                                    <CardTitle className="text-sm uppercase tracking-widest font-black">Fréquence des Alertes</CardTitle>
                                </CardHeader>
                                <CardContent className="p-8 space-y-6">
                                    <div className="space-y-3">
                                        <Label className="text-xs font-bold uppercase tracking-wider">Résumé quotidien</Label>
                                        <select defaultValue="enabled" className="w-full h-10 px-3 rounded-md bg-slate-950/50 border border-slate-800 text-white text-sm">
                                            <option value="enabled">Activé (08:00)</option>
                                            <option value="disabled">Désactivé</option>
                                        </select>
                                    </div>
                                    <div className="space-y-3">
                                        <Label className="text-xs font-bold uppercase tracking-wider">Seuil alerte montant (FCFA)</Label>
                                        <Input type="number" defaultValue="100000" className="bg-slate-950/50 border-slate-800" />
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        {/* GATEWAYS TAB */}
                        <TabsContent value="gateways" className="mt-0 space-y-6">
                            <Card className="border-slate-800 bg-slate-900/40 rounded-2xl">
                                <CardHeader className="p-8 border-b border-slate-800">
                                    <CardTitle className="text-sm uppercase tracking-widest font-black">Passerelles de Paiement</CardTitle>
                                    <CardDescription>Configuration des fournisseurs de paiement mobile</CardDescription>
                                </CardHeader>
                                <CardContent className="p-8 space-y-6">
                                    <div className="flex items-center justify-between p-6 rounded-xl bg-slate-950/40 border border-slate-800">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
                                                <Smartphone className="text-orange-500" size={20} />
                                            </div>
                                            <div>
                                                <p className="text-sm font-bold text-white">Orange Money</p>
                                                <p className="text-xs text-slate-500">Actif - 98.5% succès</p>
                                            </div>
                                        </div>
                                        <Switch defaultChecked />
                                    </div>

                                    <div className="flex items-center justify-between p-6 rounded-xl bg-slate-950/40 border border-slate-800">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                                                <Smartphone className="text-yellow-500" size={20} />
                                            </div>
                                            <div>
                                                <p className="text-sm font-bold text-white">MTN Mobile Money</p>
                                                <p className="text-xs text-slate-500">Actif - 96.2% succès</p>
                                            </div>
                                        </div>
                                        <Switch defaultChecked />
                                    </div>

                                    <div className="flex items-center justify-between p-6 rounded-xl bg-slate-950/40 border border-slate-800">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                                <Smartphone className="text-blue-500" size={20} />
                                            </div>
                                            <div>
                                                <p className="text-sm font-bold text-white">Moov Money</p>
                                                <p className="text-xs text-slate-500">Inactif</p>
                                            </div>
                                        </div>
                                        <Switch />
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="border-slate-800 bg-slate-900/40 rounded-2xl">
                                <CardHeader className="p-8 border-b border-slate-800">
                                    <CardTitle className="text-sm uppercase tracking-widest font-black">Configuration API</CardTitle>
                                </CardHeader>
                                <CardContent className="p-8 space-y-6">
                                    <div className="space-y-3">
                                        <Label className="text-xs font-bold uppercase tracking-wider">Clé API Orange Money</Label>
                                        <Input type="password" value="om_prod_key_xxxx" readOnly className="bg-slate-950/50 border-slate-800 font-mono text-xs" />
                                    </div>
                                    <div className="space-y-3">
                                        <Label className="text-xs font-bold uppercase tracking-wider">Clé API MTN</Label>
                                        <Input type="password" value="mtn_prod_key_xxxx" readOnly className="bg-slate-950/50 border-slate-800 font-mono text-xs" />
                                    </div>
                                    <div className="pt-4 border-t border-slate-800/50">
                                        <Button variant="outline" className="border-slate-800 text-[10px] font-black tracking-widest">
                                            <RefreshCw size={14} className="mr-2" />
                                            TESTER LES CONNEXIONS
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </div>
                </div>

                {/* Footer Save Button */}
                <div className="fixed bottom-10 right-10 flex gap-4 animate-in slide-in-from-right-10">
                    <Button 
                        onClick={handleSave} 
                        disabled={saving} 
                        className="h-14 px-10 font-black uppercase tracking-widest text-[10px] bg-cyan-500 hover:bg-cyan-400 text-white shadow-2xl shadow-cyan-500/20"
                    >
                        {saving ? (
                            <>
                                <RefreshCw size={16} className="mr-2 animate-spin" />
                                SYNCHRONISATION...
                            </>
                        ) : (
                            <>
                                <Save size={16} className="mr-2" />
                                ENREGISTRER
                            </>
                        )}
                    </Button>
                </div>
            </Tabs>
        </div>
    );
}
