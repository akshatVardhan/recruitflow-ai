"use client"

import * as React from "react"
import { UploadCloud } from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "@/hooks/use-toast"

export const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20 MB
export const MAX_QUEUE = 10
export const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]
export const ACCEPTED_EXTENSIONS = ".pdf,.docx"

export function isValidFileType(file: File): boolean {
  const name = file.name.toLowerCase()
  const extOk = name.endsWith(".pdf") || name.endsWith(".docx")
  return ACCEPTED_TYPES.includes(file.type) || extOk
}

export interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void
  currentCount: number
  disabled?: boolean
}

export function FileDropzone({ onFilesSelected, currentCount, disabled }: FileDropzoneProps) {
  const [dragOver, setDragOver] = React.useState(false)
  const inputRef = React.useRef<HTMLInputElement>(null)

  const validateAndEmit = React.useCallback(
    (fileList: FileList | null) => {
      if (!fileList || fileList.length === 0) return
      const incoming = Array.from(fileList)

      const remainingSlots = MAX_QUEUE - currentCount
      if (remainingSlots <= 0) {
        toast({
          variant: "destructive",
          title: "Queue full",
          description: `You can queue up to ${MAX_QUEUE} files at a time.`,
          duration: 8000,
        })
        return
      }

      const accepted: File[] = []
      for (const file of incoming) {
        if (!isValidFileType(file)) {
          toast({
            variant: "destructive",
            title: "Unsupported file type",
            description: `${file.name}: only PDF and DOCX files are allowed.`,
            duration: 8000,
          })
          continue
        }
        if (file.size > MAX_FILE_SIZE) {
          toast({
            variant: "destructive",
            title: "File too large",
            description: `${file.name}: files must be 20 MB or smaller.`,
            duration: 8000,
          })
          continue
        }
        accepted.push(file)
      }

      if (accepted.length > remainingSlots) {
        toast({
          variant: "destructive",
          title: "Too many files",
          description: `Only ${remainingSlots} more file(s) can be added (queue limit ${MAX_QUEUE}).`,
          duration: 8000,
        })
      }

      onFilesSelected(accepted.slice(0, remainingSlots))
    },
    [currentCount, onFilesSelected]
  )

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload files: drag and drop or click to browse"
      className={cn(
        "flex min-h-[160px] w-full cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 text-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        dragOver ? "border-primary bg-primary/5" : "border-border bg-card hover:bg-accent",
        disabled && "pointer-events-none opacity-60"
      )}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          inputRef.current?.click()
        }
      }}
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled) setDragOver(true)
      }}
      onDragLeave={(e) => {
        e.preventDefault()
        setDragOver(false)
      }}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        if (disabled) return
        validateAndEmit(e.dataTransfer.files)
      }}
    >
      <UploadCloud className="h-10 w-10 text-muted-foreground" aria-hidden />
      <div className="space-y-1">
        <p className="text-sm font-medium">Drag and drop files here, or click to browse</p>
        <p className="text-xs text-muted-foreground">
          PDF or DOCX only. Max 20 MB per file. Up to {MAX_QUEUE} files at once.
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_EXTENSIONS}
        className="sr-only"
        onChange={(e) => {
          validateAndEmit(e.target.files)
          // Reset so selecting the same file again re-triggers change.
          e.target.value = ""
        }}
        disabled={disabled}
      />
    </div>
  )
}

export default FileDropzone
