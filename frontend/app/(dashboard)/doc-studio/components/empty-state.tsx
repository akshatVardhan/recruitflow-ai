import { Inbox } from "lucide-react"

export function QueueEmptyState() {
  return (
    <div
      className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-zinc-800 bg-card/50 p-8 text-center"
      data-testid="queue-empty-state"
    >
      <Inbox className="h-8 w-8 text-muted-foreground" aria-hidden />
      <p className="text-sm font-medium">No files queued yet</p>
      <p className="text-xs text-muted-foreground">
        Drag and drop PDF or DOCX files above to start the upload.
      </p>
    </div>
  )
}

export default QueueEmptyState
