import { ArrowUpRight, Plus } from 'lucide-react';

interface BalanceCardProps {
    used: number;
    total: number;
    planName: string;
    onRecharge: () => void;
}

export default function BalanceCard({ used, total, planName, onRecharge }: BalanceCardProps) {
    const percentage = Math.min(Math.round((used / total) * 100), 100);

    return (
        <div className="bg-gradient-to-br from-emerald-600 to-emerald-800 rounded-3xl p-6 text-white shadow-lg relative overflow-hidden mb-6">
            {/* Background Pattern */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2 blur-2xl"></div>

            <div className="relative z-10">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <p className="text-emerald-100 text-sm font-medium mb-1">Couverture annuelle</p>
                        <h2 className="text-3xl font-bold tracking-tight">
                            {used.toLocaleString('fr-FR')} <span className="text-lg font-normal text-emerald-200">FCFA</span>
                        </h2>
                        <p className="text-xs text-emerald-200 mt-1">
                            sur {total.toLocaleString('fr-FR')} FCFA
                        </p>
                    </div>
                    <div className="bg-white/20 backdrop-blur-md px-3 py-1 rounded-full border border-white/10">
                        <span className="text-xs font-semibold">{planName}</span>
                    </div>
                </div>

                <div className="mb-6">
                    <div className="h-2 w-full bg-black/20 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-white rounded-full transition-all duration-1000 ease-out"
                            style={{ width: `${percentage}%` }}
                        ></div>
                    </div>
                    <div className="flex justify-between mt-2 text-xs text-emerald-100">
                        <span>{percentage}% utilisé</span>
                        <span>Renouvellement le 01/02</span>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <button className="bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/10 rounded-xl py-3 flex flex-col items-center justify-center transition">
                        <div className="bg-white rounded-full p-1.5 mb-1">
                            <ArrowUpRight className="w-4 h-4 text-emerald-700" />
                        </div>
                        <span className="text-xs font-medium">Scanner</span>
                    </button>
                    <button
                        onClick={onRecharge}
                        className="bg-white text-emerald-800 hover:bg-emerald-50 rounded-xl py-3 flex flex-col items-center justify-center transition font-semibold"
                    >
                        <div className="bg-emerald-100 rounded-full p-1.5 mb-1">
                            <Plus className="w-4 h-4 text-emerald-700" />
                        </div>
                        <span className="text-xs">Recharger</span>
                    </button>
                </div>
            </div>
        </div>
    );
}
