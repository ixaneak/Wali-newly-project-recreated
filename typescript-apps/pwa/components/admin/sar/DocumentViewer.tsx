"use client";
import React, { useState } from 'react';
import { X, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Download } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';

interface DocumentViewerProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    photos: string[];
}

export default function DocumentViewer({ isOpen, onClose, title, photos }: DocumentViewerProps) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [zoom, setZoom] = useState(1);

    if (!isOpen) return null;

    const displayPhotos = photos.length > 0 ? photos : [
        '/placeholder-doc-1.jpg',
        '/placeholder-doc-2.jpg',
    ];

    const prev = () => { setCurrentIndex((i) => Math.max(0, i - 1)); setZoom(1); };
    const next = () => { setCurrentIndex((i) => Math.min(displayPhotos.length - 1, i + 1)); setZoom(1); };

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    className="relative w-[90vw] max-w-4xl h-[80vh] bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden flex flex-col"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
                        <div>
                            <h3 className="text-lg font-semibold text-white">{title}</h3>
                            <p className="text-sm text-slate-400">
                                Document {currentIndex + 1} of {displayPhotos.length}
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <Button variant="outline" size="sm" className="border-slate-700" onClick={() => setZoom(z => Math.max(0.5, z - 0.25))}>
                                <ZoomOut className="w-4 h-4" />
                            </Button>
                            <span className="text-xs text-slate-400 w-12 text-center">{Math.round(zoom * 100)}%</span>
                            <Button variant="outline" size="sm" className="border-slate-700" onClick={() => setZoom(z => Math.min(3, z + 0.25))}>
                                <ZoomIn className="w-4 h-4" />
                            </Button>
                            <Button variant="outline" size="sm" className="border-slate-700">
                                <Download className="w-4 h-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={onClose}>
                                <X className="w-5 h-5" />
                            </Button>
                        </div>
                    </div>

                    {/* Image Area */}
                    <div className="flex-1 flex items-center justify-center overflow-auto bg-slate-950 relative">
                        <div className="flex items-center justify-center w-full h-full p-8" style={{ transform: `scale(${zoom})`, transition: 'transform 0.2s' }}>
                            <div className="max-w-full max-h-full rounded-lg bg-slate-800 flex items-center justify-center min-h-[300px] min-w-[400px] border border-slate-700">
                                <div className="text-center p-8">
                                    <div className="w-20 h-20 rounded-full bg-slate-700 mx-auto mb-4 flex items-center justify-center">
                                        <svg className="w-10 h-10 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                        </svg>
                                    </div>
                                    <p className="text-slate-400 text-sm">Claim Evidence Photo</p>
                                    <p className="text-slate-500 text-xs mt-1">{displayPhotos[currentIndex]}</p>
                                </div>
                            </div>
                        </div>

                        {/* Navigation */}
                        {displayPhotos.length > 1 && (
                            <>
                                <button onClick={prev} disabled={currentIndex === 0}
                                    className="absolute left-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-slate-800/80 hover:bg-slate-700 disabled:opacity-30 text-white">
                                    <ChevronLeft className="w-5 h-5" />
                                </button>
                                <button onClick={next} disabled={currentIndex === displayPhotos.length - 1}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-slate-800/80 hover:bg-slate-700 disabled:opacity-30 text-white">
                                    <ChevronRight className="w-5 h-5" />
                                </button>
                            </>
                        )}
                    </div>

                    {/* Thumbnails */}
                    {displayPhotos.length > 1 && (
                        <div className="flex gap-2 p-4 border-t border-slate-800 justify-center">
                            {displayPhotos.map((_, i) => (
                                <button key={i} onClick={() => { setCurrentIndex(i); setZoom(1); }}
                                    className={`w-12 h-12 rounded-lg border-2 transition-all flex items-center justify-center text-xs ${i === currentIndex ? 'border-cyan-500 bg-cyan-500/10' : 'border-slate-700 bg-slate-800 hover:border-slate-600'
                                        }`}>
                                    {i + 1}
                                </button>
                            ))}
                        </div>
                    )}
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
