"use client";

import { useEffect, useState } from "react";
import { Heart, ChevronRight } from "lucide-react";

const TIPS = [
    {
        id: 1,
        title: "Hydratation",
        text: "Buvez au moins 1,5L d'eau par jour pour rester en forme.",
        color: "bg-blue-100 dark:bg-blue-900/30",
        textColor: "text-blue-700 dark:text-blue-300",
        iconColor: "text-blue-500",
    },
    {
        id: 2,
        title: "Vaccination",
        text: "Vérifiez que vos vaccins sont à jour, surtout pour les enfants.",
        color: "bg-emerald-100 dark:bg-emerald-900/30",
        textColor: "text-emerald-700 dark:text-emerald-300",
        iconColor: "text-emerald-500",
    },
    {
        id: 3,
        title: "Activité Physique",
        text: "30 minutes de marche par jour réduisent les risques cardiaques.",
        color: "bg-orange-100 dark:bg-orange-900/30",
        textColor: "text-orange-700 dark:text-orange-300",
        iconColor: "text-orange-500",
    },
];

export default function HealthTipsCarousel() {
    const [current, setCurrent] = useState(0);

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrent((prev) => (prev + 1) % TIPS.length);
        }, 5000); // 5 seconds per slide

        return () => clearInterval(timer);
    }, []);

    const tip = TIPS[current];

    return (
        <div className="mb-6">
            <div className="flex justify-between items-center mb-2 px-1">
                <h3 className="font-bold text-gray-800 dark:text-white flex items-center gap-2">
                    <Heart className="w-4 h-4 text-red-500 fill-red-500" />
                    Conseil Santé
                </h3>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                    {current + 1}/{TIPS.length}
                </span>
            </div>

            <div className={`relative overflow-hidden rounded-2xl p-4 transition-colors duration-500 ${tip.color}`}>
                <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-full bg-white/50 dark:bg-black/20 ${tip.iconColor}`}>
                        <Heart className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                        <h4 className={`font-semibold text-sm mb-1 ${tip.textColor}`}>
                            {tip.title}
                        </h4>
                        <p className={`text-xs opacity-90 leading-relaxed ${tip.textColor}`}>
                            {tip.text}
                        </p>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="absolute bottom-0 left-0 h-1 bg-white/30 w-full">
                    <div
                        key={tip.id} // Reset animation on change
                        className="h-full bg-current opacity-50 origin-left animate-[progress_5s_linear]"
                        style={{ color: "currentColor" }}
                    ></div>
                </div>
            </div>
        </div>
    );
}
