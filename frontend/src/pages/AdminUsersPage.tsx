import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { UserCog, UserPlus } from 'lucide-react'
import { adminApi } from '../api/endpoints'
import { useAuth } from '../contexts/AuthContext'
import type { AdminUser } from '../api/types'
import { Alert, Badge, Button, Card, Checkbox, EmptyState, Field, Input, Modal, PageHeader, Pager, Table } from '../components/ui'

const emptyInviteForm = { email: '', full_name: '', password: '', role_ids: [] as string[], is_superuser: false }
const USERS_PAGE_SIZE = 20

export function AdminUsersPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { user: currentUser, impersonate } = useAuth()
  const [usersOffset, setUsersOffset] = useState(0)
  const [impersonateError, setImpersonateError] = useState<string | null>(null)
  const [isImpersonating, setIsImpersonating] = useState(false)

  const { data: usersPage } = useQuery({
    queryKey: ['admin-users', usersOffset],
    queryFn: () => adminApi.listUsers({ limit: USERS_PAGE_SIZE, offset: usersOffset }),
  })
  const users = usersPage?.items ?? []
  const { data: roles = [] } = useQuery({ queryKey: ['admin-roles'], queryFn: adminApi.listRoles })

  const [isInviteOpen, setIsInviteOpen] = useState(false)
  const [inviteForm, setInviteForm] = useState(emptyInviteForm)
  const [inviteError, setInviteError] = useState<string | null>(null)

  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [editRoleIds, setEditRoleIds] = useState<string[]>([])

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin-users'] })

  const createUser = useMutation({
    mutationFn: () => adminApi.createUser(inviteForm),
    onSuccess: () => {
      invalidate()
      setIsInviteOpen(false)
      setInviteForm(emptyInviteForm)
      setInviteError(null)
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setInviteError(message ?? 'Could not create user.')
    },
  })

  const updateUser = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof adminApi.updateUser>[1] }) =>
      adminApi.updateUser(id, payload),
    onSuccess: () => {
      invalidate()
      setEditingUser(null)
    },
  })

  const toggleRole = (roleId: string, checked: boolean) => {
    setInviteForm((prev) => ({
      ...prev,
      role_ids: checked ? [...prev.role_ids, roleId] : prev.role_ids.filter((id) => id !== roleId),
    }))
  }

  const openEdit = (u: AdminUser) => {
    setEditingUser(u)
    setEditRoleIds(u.role_ids)
    setImpersonateError(null)
  }

  const handleImpersonate = async (targetUserId: string) => {
    setImpersonateError(null)
    setIsImpersonating(true)
    try {
      await impersonate(targetUserId)
      setEditingUser(null)
      navigate('/')
    } catch (err: unknown) {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setImpersonateError(message ?? 'Could not start impersonating this user.')
    } finally {
      setIsImpersonating(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Users"
        description="Invite teammates and control what they can see and do."
        actions={
          <Button onClick={() => setIsInviteOpen(true)}>
            <UserPlus className="h-4 w-4" /> Invite user
          </Button>
        }
      />

      <Card>
        {users.length === 0 ? (
          <EmptyState message="No users yet." />
        ) : (
          <>
          <Table headers={['Name', 'Email', 'Roles', 'Status', '']}>
            {users.map((u) => (
              <tr key={u.id}>
                <td className="px-3 py-2 font-medium text-slate-800">
                  {u.full_name}
                  {u.is_superuser && (
                    <Badge tone="purple">
                      <span className="ml-1">Superuser</span>
                    </Badge>
                  )}
                </td>
                <td className="px-3 py-2 text-slate-500">{u.email}</td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
                    {u.role_names.length === 0 ? (
                      <span className="text-slate-400">—</span>
                    ) : (
                      u.role_names.map((name) => (
                        <Badge key={name} tone="blue">
                          {name}
                        </Badge>
                      ))
                    )}
                  </div>
                </td>
                <td className="px-3 py-2">
                  <Badge tone={u.is_active ? 'green' : 'slate'}>{u.is_active ? 'Active' : 'Inactive'}</Badge>
                </td>
                <td className="px-3 py-2">
                  <Button size="sm" variant="secondary" onClick={() => openEdit(u)}>
                    Edit
                  </Button>
                </td>
              </tr>
            ))}
          </Table>
          <Pager offset={usersOffset} limit={USERS_PAGE_SIZE} total={usersPage?.total ?? 0} onOffsetChange={setUsersOffset} />
          </>
        )}
      </Card>

      {isInviteOpen && (
        <Modal title="Invite user" onClose={() => setIsInviteOpen(false)}>
          {inviteError && <Alert onDismiss={() => setInviteError(null)}>{inviteError}</Alert>}
          <form
            className="flex flex-col gap-3"
            onSubmit={(e) => {
              e.preventDefault()
              createUser.mutate()
            }}
          >
            <Field label="Full name">
              <Input required value={inviteForm.full_name} onChange={(e) => setInviteForm({ ...inviteForm, full_name: e.target.value })} />
            </Field>
            <Field label="Email">
              <Input
                type="email"
                required
                value={inviteForm.email}
                onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
              />
            </Field>
            <Field label="Temporary password">
              <Input
                type="password"
                required
                minLength={8}
                value={inviteForm.password}
                onChange={(e) => setInviteForm({ ...inviteForm, password: e.target.value })}
              />
            </Field>
            <div>
              <p className="mb-1 text-sm font-medium text-slate-600">Roles</p>
              <div className="flex flex-col gap-1.5 rounded-lg border border-slate-200 p-3">
                {roles.length === 0 ? (
                  <p className="text-sm text-slate-400">No roles yet — create one on the Roles page.</p>
                ) : (
                  roles.map((r) => (
                    <Checkbox
                      key={r.id}
                      label={r.name}
                      checked={inviteForm.role_ids.includes(r.id)}
                      onChange={(e) => toggleRole(r.id, e.target.checked)}
                    />
                  ))
                )}
              </div>
            </div>
            <Checkbox
              label="Superuser (bypasses all permission checks)"
              checked={inviteForm.is_superuser}
              onChange={(e) => setInviteForm({ ...inviteForm, is_superuser: e.target.checked })}
            />
            <Button type="submit" disabled={createUser.isPending} className="mt-1">
              {createUser.isPending ? 'Creating…' : 'Create user'}
            </Button>
          </form>
        </Modal>
      )}

      {editingUser && (
        <Modal title={`Edit ${editingUser.full_name}`} onClose={() => setEditingUser(null)}>
          <form
            className="flex flex-col gap-3"
            onSubmit={(e) => {
              e.preventDefault()
              updateUser.mutate({ id: editingUser.id, payload: { role_ids: editRoleIds } })
            }}
          >
            <div>
              <p className="mb-1 text-sm font-medium text-slate-600">Roles</p>
              <div className="flex flex-col gap-1.5 rounded-lg border border-slate-200 p-3">
                {roles.map((r) => (
                  <Checkbox
                    key={r.id}
                    label={r.name}
                    checked={editRoleIds.includes(r.id)}
                    onChange={(e) =>
                      setEditRoleIds((prev) => (e.target.checked ? [...prev, r.id] : prev.filter((id) => id !== r.id)))
                    }
                  />
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-slate-200 p-3">
              <span className="text-sm text-slate-700">Active</span>
              <Button
                type="button"
                size="sm"
                variant={editingUser.id === currentUser?.id ? 'secondary' : editingUser.is_active ? 'danger' : 'secondary'}
                disabled={editingUser.id === currentUser?.id}
                onClick={() =>
                  updateUser.mutate(
                    { id: editingUser.id, payload: { is_active: !editingUser.is_active } },
                    { onSuccess: () => setEditingUser(null) },
                  )
                }
              >
                {editingUser.is_active ? 'Deactivate' : 'Activate'}
              </Button>
            </div>
            {editingUser.id === currentUser?.id && (
              <p className="text-xs text-slate-400">You can't deactivate your own account.</p>
            )}

            <Button type="submit" disabled={updateUser.isPending} className="mt-1">
              {updateUser.isPending ? 'Saving…' : 'Save roles'}
            </Button>
          </form>

          {currentUser?.is_superuser && editingUser.id !== currentUser.id && (
            <div className="mt-4 flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 p-3">
              <div>
                <p className="text-sm font-medium text-amber-900">Impersonate this user</p>
                <p className="text-xs text-amber-700">
                  {editingUser.is_active
                    ? 'See exactly what they see — you can return to your own account at any time.'
                    : 'Activate this user first to impersonate them.'}
                </p>
              </div>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                disabled={!editingUser.is_active || isImpersonating}
                onClick={() => handleImpersonate(editingUser.id)}
              >
                <UserCog className="h-3.5 w-3.5" /> {isImpersonating ? 'Switching…' : 'Impersonate'}
              </Button>
            </div>
          )}
          {impersonateError && (
            <div className="mt-3">
              <Alert onDismiss={() => setImpersonateError(null)}>{impersonateError}</Alert>
            </div>
          )}
        </Modal>
      )}
    </div>
  )
}
