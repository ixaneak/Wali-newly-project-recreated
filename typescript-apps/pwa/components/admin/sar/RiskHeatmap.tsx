"use client";
import React from 'react';
import { cn } from '@/lib/utils';

interface HeatmapCell {
    label: string;
    value: number;
    count: number;
}

interface RiskHeatmapProps {
    data?: HeatmapCell[];
}

const DEFAULT_DATA: HeatmapCell[] = [
    { label: 'Structuring', value: 78, count: 12 },
    { label: 'Rapid Claim', value: 65, count: 8 },
    { label: 'Round Numbers', value: 22, count: 35 },
    { label: 'High Velocity', value: 54, count: 5 },
    { label: 'Threshold', value: 88, count: 3 },
    { label: 'Identity Mismatch', value: 42, count: 15 },
    { label: 'Third-Party Pay', value: 38, count: 9 },
    { label: 'Doc Forgery', value: 91, count: 2 },
    { label: 'Sanctions Match', value: 95, count: 1 },
    { label: 'PEP Match', value: 70, count: 4 },
    { label: 'Geo Anomaly', value: 48, count: 11 },
    { label: 'Freq. Pattern', value: 33, count: 18 },
];

function getHeatColor(value: number): string {
    if (value >= 80) return 'bg-red-500/80 border-red-500/40 text-white';
    if (value >= 60) return 'bg-orange-500/60 border-orange-500/40 text-white';
    if (value >= 40) return 'bg-amber-500/40 border-amber-500/30 text-amber-100';
    if (value >= 20) return 'bg-yellow-500/20 border-yellow-500/20 text-yellow-200';
    return 'bg-emerald-500/15 border-emerald-500/20 text-emerald-200';
}

export default function RiskHeatmap({ data = DEFAULT_DATA }: RiskHeatmapProps) {
    return (
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
            {data.map((cell) => (
                <div
                    key={cell.label}
                    className={cn(
                        "p-3 rounded-xl border transition-all hover:scale-105 cursor-default group",
                        getHeatColor(cell.value)
                    )}
                >
                    <div className="text-xs font-medium truncate">{cell.label}</div>
                    <div className="text-2xl font-black mt-1">{cell.value}</div>
                    <div className="text-[10px] opacity-70">{cell.count} events</div>
                </div>
            ))}
        </div>
    );
}
