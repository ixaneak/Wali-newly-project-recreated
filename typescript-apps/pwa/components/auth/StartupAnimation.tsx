'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

interface StartupAnimationProps {
    onComplete: () => void;
}

export default function StartupAnimation({ onComplete }: StartupAnimationProps) {
    const [stage, setStage] = useState(0);

    useEffect(() => {
        // Stage 1: Breathe (0-1200ms)
        // Stage 2: Nature Elements (800-4000ms)
        // Stage 3: Stabilize (3000-4500ms)

        const timer1 = setTimeout(() => setStage(1), 800);
        const timer2 = setTimeout(() => setStage(2), 3000);
        const timer3 = setTimeout(() => onComplete(), 4500);

        return () => {
            clearTimeout(timer1);
            clearTimeout(timer2);
            clearTimeout(timer3);
        };
    }, [onComplete]);

    // Simplified leaf path
    const leafPath = "M12 2C8 6 2 12 2 18c0 4 3 7 7 7s7-3 7-7c0-6-6-12-10-16z";

    return (
        <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.8 } }}
            className="fixed inset-0 z-[100] flex items-center justify-center overflow-hidden bg-gradient-to-br from-teal-900 via-emerald-800 to-green-900"
        >
            {/* Background Gradient Animation */}
            <motion.div
                className="absolute inset-0 z-0 bg-gradient-to-br from-teal-900 via-emerald-800 to-green-900"
                animate={{
                    background: [
                        "linear-gradient(135deg, #115e59 0%, #059669 50%, #047857 100%)", // darker start
                        "linear-gradient(135deg, #0d9488 0%, #34d399 50%, #10b981 100%)", // lighter middle
                        "linear-gradient(135deg, #115e59 0%, #059669 50%, #047857 100%)"  // back to dark
                    ]
                }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            />

            {/* Blurred overlay for depth */}
            <div className="absolute inset-0 z-0 backdrop-blur-[2px] bg-black/10" />

            {/* Nature Elements (Phase 2) */}
            <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
                {stage >= 1 && (
                    <>
                        {/* Generating 8 leaves with random paths */}
                        {[...Array(8)].map((_, i) => (
                            <motion.div
                                key={`leaf-${i}`}
                                className="absolute w-8 h-8 text-emerald-300 fill-current opacity-40"
                                initial={{
                                    x: -50,
                                    y: Math.random() * 800, // Explicit random range for simplification
                                    opacity: 0,
                                    rotate: 0
                                }}
                                animate={{
                                    x: typeof window !== 'undefined' ? window.innerWidth + 50 : 1000,
                                    y: Math.random() * 800,
                                    opacity: [0, 0.4, 0],
                                    rotate: [0, 90, 180]
                                }}
                                transition={{
                                    duration: 4 + Math.random() * 2,
                                    ease: "easeInOut",
                                    delay: Math.random() * 0.5
                                }}
                            >
                                <svg viewBox="0 0 24 24" className="w-full h-full fill-current">
                                    <path d={leafPath} />
                                </svg>
                            </motion.div>
                        ))}

                        {/* Bokeh Particles */}
                        {[...Array(12)].map((_, i) => (
                            <motion.div
                                key={`bokeh-${i}`}
                                className="absolute rounded-full bg-white blur-sm opacity-20"
                                style={{
                                    width: Math.random() * 10 + 5,
                                    height: Math.random() * 10 + 5,
                                    left: `${Math.random() * 100}%`,
                                    top: `${Math.random() * 100}%`,
                                }}
                                animate={{
                                    y: [0, -100],
                                    opacity: [0, 0.3, 0]
                                }}
                                transition={{
                                    duration: 2 + Math.random() * 3,
                                    repeat: Infinity,
                                    delay: Math.random() * 2
                                }}
                            />
                        ))}
                    </>
                )}
            </div>

            {/* Main Content Container */}
            <div className="relative z-10 flex flex-col items-center justify-center w-full h-full">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={stage >= 2 ? {
                        scale: 1,
                        opacity: 1,
                        y: -40
                    } : {
                        scale: [0.8, 1.05, 1],
                        opacity: 1,
                        y: 0
                    }}
                    transition={{
                        duration: stage >= 2 ? 0.8 : 1.2,
                        times: stage >= 2 ? undefined : [0, 0.6, 1],
                        ease: "easeInOut"
                    }}
                    className="flex items-center justify-center"
                >
                    <div className="bg-white/95 backdrop-blur-2xl p-6 rounded-[24px] shadow-2xl border border-white/10">
                        <svg viewBox="0 0 48 48" className="w-20 h-20">
                            <rect x="2" y="2" width="44" height="44" rx="14" fill="white" className="opacity-0" />
                            {/* Note: In startup animation, maybe we just show the W? Or the full card icon? 
                        User said "Logo starts at 0.8 scale". 
                        The login page has a white rect background. I'll keep the white rect but make it part of the SVG or container.
                        The login page SVG has: rect fill="white".
                    */}
                            <rect x="2" y="2" width="44" height="44" rx="14" fill="white" />
                            <path
                                d="M12 28 Q18 16 24 28 Q30 16 36 28"
                                stroke="#00b386"
                                strokeWidth="5.5"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                fill="none"
                            />
                        </svg>
                    </div>
                </motion.div>

                {/* Text Fade In (Phase 3) */}
                <AnimatePresence>
                    {stage >= 2 && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.8, delay: 0.2 }}
                            className="absolute top-[55%] flex flex-col items-center"
                        >
                            <h1 className="text-5xl font-light text-white tracking-[0.5em] ml-[0.5em] mb-8 font-sans">
                                wali
                            </h1>

                            {/* Circular Loading Indicator */}
                            <motion.div
                                className="w-6 h-6 rounded-full border-2 border-emerald-400/30 border-t-emerald-400"
                                animate={{ rotate: 360 }}
                                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}
