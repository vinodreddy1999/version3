import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, ShieldCheck, Trash2 } from 'lucide-react'
import { adminApi } from '../api/endpoints'
import type { Role } from '../api/types'
import { errorMessage } from '../lib/apiClient'
import { Alert, Badge, Button, Card, Checkbox, EmptyState, Field, Input, Modal, PageHeader } from '../components/ui'

function groupPermissions(codes: string[]) {
  const groups: Record<string, string[]> = {}
  for (const code of codes) {
    const [module] = code.split(':')
    groups[module] ??= []
    groups[module].push(code)
  }
  return groups
}

const emptyForm = { name: '', permission_codes: [] as string[] }

export function AdminRolesPage() {
  const queryClient = useQueryClient()
  const { data: roles = [] } = useQuery({ queryKey: ['admin-roles'], queryFn: adminApi.listRoles })
  const { data: permissions = [] } = useQuery({ queryKey: ['admin-permissions'], queryFn: adminApi.listPermissions })
  const groups = groupPermissions(permissions.map((p) => p.code))

  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState(emptyForm)
  const [createError, setCreateError] = useState<string | null>(null)
  const [editingRole, setEditingRole] = useState<Role | null>(null)
  const [editPermissionCodes, setEditPermissionCodes] = useState<string[]>([])

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin-roles'] })

  const createRole = useMutation({
    mutationFn: () => adminApi.createRole(createForm),
    onSuccess: () => {
      invalidate()
      setIsCreateOpen(false)
      setCreateForm(emptyForm)
      setCreateError(null)
    },
    onError: (err: unknown) => setCreateError(errorMessage(err, 'Could not create role.')),
  })

  const updateRole = useMutation({
    mutationFn: () => adminApi.updateRole(editingRole!.id, { permission_codes: editPermissionCodes }),
    onSuccess: () => {
      invalidate()
      setEditingRole(null)
    },
  })

  const deleteRole = useMutation({
    mutationFn: (id: string) => adminApi.deleteRole(id),
    onSuccess: invalidate,
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Roles"
        description="Bundle permissions into roles, then assign them to users."
        actions={
          <Button onClick={() => setIsCreateOpen(true)}>
            <Plus className="h-4 w-4" /> New role
          </Button>
        }
      />

      {roles.length === 0 ? (
        <Card>
          <EmptyState message="No roles yet." />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {roles.map((r) => (
            <Card key={r.id} icon={<ShieldCheck className="h-4 w-4" />}>
              <div className="mb-3 flex items-start justify-between">
                <div>
                  <p className="font-semibold text-slate-800">{r.name}</p>
                  {r.is_system && <Badge tone="purple">System</Badge>}
                </div>
                {!r.is_system && (
                  <button
                    onClick={() => {
                      if (confirm(`Delete role "${r.name}"?`)) deleteRole.mutate(r.id)
                    }}
                    className="text-slate-300 hover:text-red-600"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
              <p className="mb-3 text-xs text-slate-400">{r.permission_codes.length} permission(s)</p>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  setEditingRole(r)
                  setEditPermissionCodes(r.permission_codes)
                }}
              >
                Edit permissions
              </Button>
            </Card>
          ))}
        </div>
      )}

      {isCreateOpen && (
        <Modal title="New role" onClose={() => setIsCreateOpen(false)}>
          {createError && <Alert onDismiss={() => setCreateError(null)}>{createError}</Alert>}
          <form
            className="flex flex-col gap-3"
            onSubmit={(e) => {
              e.preventDefault()
              createRole.mutate()
            }}
          >
            <Field label="Role name">
              <Input required value={createForm.name} onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })} />
            </Field>
            <div className="max-h-72 overflow-y-auto rounded-lg border border-slate-200 p-3">
              {Object.entries(groups).map(([module, codes]) => (
                <div key={module} className="mb-3 last:mb-0">
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{module}</p>
                  <div className="flex flex-col gap-1">
                    {codes.map((code) => (
                      <Checkbox
                        key={code}
                        label={code}
                        checked={createForm.permission_codes.includes(code)}
                        onChange={(e) =>
                          setCreateForm((prev) => ({
                            ...prev,
                            permission_codes: e.target.checked
                              ? [...prev.permission_codes, code]
                              : prev.permission_codes.filter((c) => c !== code),
                          }))
                        }
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <Button type="submit" disabled={createRole.isPending} className="mt-1">
              {createRole.isPending ? 'Creating…' : 'Create role'}
            </Button>
          </form>
        </Modal>
      )}

      {editingRole && (
        <Modal title={`Edit "${editingRole.name}"`} onClose={() => setEditingRole(null)}>
          <form
            className="flex flex-col gap-3"
            onSubmit={(e) => {
              e.preventDefault()
              updateRole.mutate()
            }}
          >
            <div className="max-h-72 overflow-y-auto rounded-lg border border-slate-200 p-3">
              {Object.entries(groups).map(([module, codes]) => (
                <div key={module} className="mb-3 last:mb-0">
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{module}</p>
                  <div className="flex flex-col gap-1">
                    {codes.map((code) => (
                      <Checkbox
                        key={code}
                        label={code}
                        checked={editPermissionCodes.includes(code)}
                        onChange={(e) =>
                          setEditPermissionCodes((prev) =>
                            e.target.checked ? [...prev, code] : prev.filter((c) => c !== code),
                          )
                        }
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <Button type="submit" disabled={updateRole.isPending} className="mt-1">
              {updateRole.isPending ? 'Saving…' : 'Save permissions'}
            </Button>
          </form>
        </Modal>
      )}
    </div>
  )
}
