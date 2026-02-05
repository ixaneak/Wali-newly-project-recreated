"use client"

import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"

export function ThemeToggle() {
    const { theme, setTheme } = useTheme()
    const [mounted, setMounted] = React.useState(false)

    React.useEffect(() => {
        setMounted(true)
    }, [])

    if (!mounted) {
        return <div className="w-12 h-6" /> // Placeholder to prevent layout shift
    }

    const isDark = theme === "dark"

    return (
        <button
            onClick={() => setTheme(isDark ? "light" : "dark")}
            className={`
                relative w-12 h-6 rounded-full transition-colors duration-200 
                focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2
                dark:focus:ring-offset-slate-900
                ${isDark ? 'bg-emerald-600' : 'bg-gray-200'}
            `}
            aria-label="Toggle theme"
        >
            {/* Toggle Knob */}
            <div className={`
                absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm 
                transform transition-transform duration-200 
                flex items-center justify-center
                ${isDark ? 'translate-x-6' : 'translate-x-0.5'}
            `}>
                {isDark ? (
                    <Moon className="w-3 h-3 text-emerald-600" />
                ) : (
                    <Sun className="w-3 h-3 text-yellow-500" />
                )}
            </div>
        </button>
    )
}
