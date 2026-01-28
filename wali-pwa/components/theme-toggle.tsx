"use client"

import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"

export function ThemeToggle() {
    const { theme, setTheme } = useTheme()

    return (
        <button
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            className="rounded-full w-12 h-6 bg-gray-200 dark:bg-gray-700 relative transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            aria-label="Toggle theme"
        >
            <div className={`
          absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow-sm transform transition-transform duration-200 flex items-center justify-center
          ${theme === "dark" ? "translate-x-6" : "translate-x-0"}
      `}>
                {theme === "dark" ? (
                    <Moon className="w-3 h-3 text-slate-900" />
                ) : (
                    <Sun className="w-3 h-3 text-yellow-500" />
                )}
            </div>
        </button>
    )
}
