import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

export type Theme = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'todaynew-admin:theme'

interface ThemeState {
  theme: Theme
  setTheme: (t: Theme) => void
}

const ThemeContext = createContext<ThemeState | null>(null)

function syncNativeSystemBars(dark: boolean) {
  const cap = (window as { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor
  if (!cap?.isNativePlatform?.()) return
  void import('@capacitor/core').then(({ registerPlugin }) => {
    const systemBars = registerPlugin<{
      setStyle: (options: { bar: 'StatusBar' | 'NavigationBar'; style: 'LIGHT' | 'DARK' }) => Promise<void>
    }>('SystemBars')
    const style = dark ? 'DARK' : 'LIGHT'
    void systemBars.setStyle({ bar: 'StatusBar', style }).catch(() => {})
    void systemBars.setStyle({ bar: 'NavigationBar', style }).catch(() => {})
  })
}

function readTheme(): Theme {
  const v = localStorage.getItem(STORAGE_KEY)
  return v === 'light' || v === 'dark' ? v : 'system'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(readTheme)

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const apply = () => {
      const dark = theme === 'dark' || (theme === 'system' && media.matches)
      document.documentElement.classList.toggle('dark', dark)
      syncNativeSystemBars(dark)
    }
    apply()
    if (theme !== 'system') return
    media.addEventListener('change', apply)
    return () => media.removeEventListener('change', apply)
  }, [theme])

  const setTheme = (t: Theme) => {
    localStorage.setItem(STORAGE_KEY, t)
    setThemeState(t)
  }

  return <ThemeContext value={{ theme, setTheme }}>{children}</ThemeContext>
}

// oxlint-disable-next-line react/only-export-components
export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme 必须在 ThemeProvider 内使用')
  return ctx
}
