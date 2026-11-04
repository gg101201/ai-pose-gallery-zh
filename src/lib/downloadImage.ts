import { registerPlugin } from '@capacitor/core'
import { toast } from '@/lib/notifications'

interface ImageSaverPlugin {
  save(options: { src: string; filename: string }): Promise<{ path: string }>
}

const ImageSaver = registerPlugin<ImageSaverPlugin>('ImageSaver')

function isNativeApp(): boolean {
  const capacitor = (globalThis as { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor
  return Boolean(capacitor?.isNativePlatform?.())
}

/** 把相对路径解析成 App 内的 https://localhost/...，避免原生插件拿不到当前页面地址。 */
function resolveSource(src: string): string {
  if (/^(data:|blob:|https?:\/\/)/i.test(src)) return src
  return new URL(src, window.location.href).href
}

function fileNameFromSource(src: string): string {
  if (src.startsWith('data:')) {
    const mime = src.slice(5, src.indexOf(';'))
    const extension = (mime.split('/')[1] || 'png').replace('jpeg', 'jpg')
    return `image.${extension}`
  }
  try {
    const name = decodeURIComponent(new URL(src, window.location.href).pathname.split('/').pop() || '')
    return name || 'image.jpg'
  } catch {
    return 'image.jpg'
  }
}

function withExtension(name: string, src: string): string {
  if (/\.[a-z0-9]{2,5}$/i.test(name)) return name
  const guessed = fileNameFromSource(src)
  const dot = guessed.lastIndexOf('.')
  return dot > 0 ? `${name}${guessed.slice(dot)}` : name
}

function blobToDataUrl(src: string): Promise<string> {
  return fetch(src)
    .then((response) => response.blob())
    .then(
      (blob) =>
        new Promise<string>((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => resolve(String(reader.result))
          reader.onerror = () => reject(reader.error || new Error('读取图片失败'))
          reader.readAsDataURL(blob)
        })
    )
}

/**
 * 保存图片。原生 App 走 ImageSaver 插件写入系统「下载/AI-Figure-Atlas」；
 * 浏览器里退化为普通的 <a download>。
 */
export async function downloadImage(src: string, filename?: string): Promise<void> {
  const name = withExtension(filename || fileNameFromSource(src), src)
  try {
    if (isNativeApp()) {
      let payload = resolveSource(src)
      if (payload.startsWith('blob:')) payload = await blobToDataUrl(payload)
      const result = await ImageSaver.save({ src: payload, filename: name })
      toast.success(`已保存到 ${result.path}`)
      return
    }
    const anchor = document.createElement('a')
    anchor.href = src
    anchor.download = name
    anchor.rel = 'noopener'
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    toast.success('已开始下载')
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '保存图片失败')
  }
}
