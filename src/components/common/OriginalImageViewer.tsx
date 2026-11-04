import { DownloadIcon, XIcon } from 'lucide-react'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { downloadImage } from '@/lib/downloadImage'

interface OriginalImageViewerProps {
  src: string | null
  name?: string
  onClose: () => void
}

export function OriginalImageViewer({ src, name, onClose }: OriginalImageViewerProps) {
  useEffect(() => {
    if (!src) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [src, onClose])

  if (!src) return null

  return (
    <div
      className="fixed inset-0 z-[60] flex flex-col bg-black/95"
      role="dialog"
      aria-modal="true"
      aria-label="原图预览"
    >
      <div
        className="flex shrink-0 items-center justify-between gap-2 px-3 pb-2"
        style={{ paddingTop: 'calc(env(safe-area-inset-top, 0px) + 0.5rem)' }}
      >
        <span className="truncate text-sm font-medium text-white/90">{name || '原图预览'}</span>
        <div className="flex shrink-0 items-center gap-1">
          <Button
            size="icon-sm"
            variant="ghost"
            className="text-white hover:bg-white/15 hover:text-white"
            onClick={() => void downloadImage(src, name)}
          >
            <DownloadIcon className="size-4" />
            <span className="sr-only">下载原图</span>
          </Button>
          <Button
            size="icon-sm"
            variant="ghost"
            className="text-white hover:bg-white/15 hover:text-white"
            onClick={onClose}
          >
            <XIcon className="size-4" />
            <span className="sr-only">关闭</span>
          </Button>
        </div>
      </div>
      <div
        className="flex min-h-0 flex-1 items-center justify-center overflow-hidden px-3"
        style={{ paddingBottom: 'calc(env(safe-area-inset-bottom, 0px) + 0.75rem)' }}
      >
        <img
          src={src}
          alt={name || '原图'}
          className="max-h-full max-w-full rounded-lg object-contain"
          draggable={false}
        />
      </div>
    </div>
  )
}
