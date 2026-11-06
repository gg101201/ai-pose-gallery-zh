export interface SafeAreaInsets {
  top: number
  right: number
  bottom: number
  left: number
}

const ZERO: SafeAreaInsets = { top: 0, right: 0, bottom: 0, left: 0 }

/**
 * Capacitor SystemBars 会通过 --safe-area-inset-* 注入 Android 状态栏/导航栏高度。
 * 在 Web 上这些变量不存在，返回 0。
 */
export function readSafeAreaInsets(): SafeAreaInsets {
  if (typeof document === 'undefined') return ZERO
  const style = getComputedStyle(document.documentElement)
  const read = (name: string) => {
    const value = Number.parseFloat(style.getPropertyValue(name))
    return Number.isFinite(value) ? value : 0
  }
  return {
    top: read('--safe-area-inset-top'),
    right: read('--safe-area-inset-right'),
    bottom: read('--safe-area-inset-bottom'),
    left: read('--safe-area-inset-left'),
  }
}
