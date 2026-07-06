"use client"

import * as React from "react"
import { Loader2, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import type { Client } from "@/types/api"

interface ClientSelectorProps {
  clients: Client[]
  loading: boolean
  selectedId: string | null
  onSelect: (id: string) => void
  onCreate: (name: string) => Promise<void>
  creating: boolean
}

export function ClientSelector({
  clients,
  loading,
  selectedId,
  onSelect,
  onCreate,
  creating,
}: ClientSelectorProps) {
  // null = no explicit user choice yet, so the form defaults to visible
  // whenever there are no clients - derived during render, not in an
  // effect, so it stays correct as `clients` arrives asynchronously.
  const [formToggle, setFormToggle] = React.useState<boolean | null>(null)
  const showCreateForm = formToggle ?? clients.length === 0
  const [name, setName] = React.useState("")

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    await onCreate(name.trim())
    setName("")
    setFormToggle(false)
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading clients...
      </div>
    )
  }

  return (
    <div className="space-y-1.5" data-testid="client-selector">
      <Label htmlFor="client-select">Client</Label>
      {!showCreateForm ? (
        <div className="flex items-center gap-2">
          <Select
            id="client-select"
            value={selectedId ?? ""}
            onChange={(e) => onSelect(e.target.value)}
            data-testid="client-select-input"
            className="max-w-xs"
          >
            {clients.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setFormToggle(true)}
            data-testid="show-create-client"
          >
            <Plus className="mr-1 h-4 w-4" />
            New client
          </Button>
        </div>
      ) : (
        <form onSubmit={(e) => void handleCreate(e)} className="flex items-center gap-2">
          <Input
            placeholder="Client name (e.g. Acme Staffing)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="max-w-xs"
            data-testid="new-client-name"
          />
          <Button type="submit" size="sm" disabled={creating || !name.trim()}>
            {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Create"}
          </Button>
          {clients.length > 0 ? (
            <Button type="button" variant="ghost" size="sm" onClick={() => setFormToggle(false)}>
              Cancel
            </Button>
          ) : null}
        </form>
      )}
    </div>
  )
}
