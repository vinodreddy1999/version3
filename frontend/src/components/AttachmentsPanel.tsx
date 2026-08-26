import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Paperclip } from 'lucide-react'
import { attachmentsApi } from '../api/endpoints'
import type { AttachmentEntityType } from '../api/types'
import { errorMessage } from '../lib/apiClient'
import { Button } from './ui'

export function AttachmentsPanel({ entityType, entityId }: { entityType: AttachmentEntityType; entityId: string }) {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)

  const queryKey = ['attachments', entityType, entityId]
  const { data: attachments = [] } = useQuery({
    queryKey,
    queryFn: () => attachmentsApi.list(entityType, entityId),
  })

  const upload = useMutation({
    mutationFn: (file: File) => attachmentsApi.upload(entityType, entityId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
      setError(null)
    },
    onError: (err: unknown) => setError(errorMessage(err, 'Could not upload file.')),
  })

  return (
    <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
      <Paperclip className="h-3.5 w-3.5 shrink-0 text-slate-400" />
      {attachments.map((a) => (
        <button
          key={a.id}
          type="button"
          onClick={() => attachmentsApi.download(a)}
          className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-slate-600 hover:bg-slate-200"
        >
          <Download className="h-3 w-3" /> {a.filename}
        </button>
      ))}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) upload.mutate(file)
          e.target.value = ''
        }}
      />
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => fileInputRef.current?.click()}
        disabled={upload.isPending}
      >
        + Attach file
      </Button>
      {error && <span className="text-red-600">{error}</span>}
    </div>
  )
}
