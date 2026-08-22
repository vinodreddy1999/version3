import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Building2, Factory } from 'lucide-react'
import { orgApi } from '../api/endpoints'
import { Badge, Button, Card, Input, PageHeader, Select, Table, EmptyState } from '../components/ui'

export function OrgPage() {
  const queryClient = useQueryClient()
  const { data: companies = [] } = useQuery({ queryKey: ['companies'], queryFn: orgApi.listCompanies })
  const { data: plants = [] } = useQuery({ queryKey: ['plants'], queryFn: () => orgApi.listPlants() })

  const [companyForm, setCompanyForm] = useState({ name: '', code: '' })
  const [plantForm, setPlantForm] = useState({ company_id: '', name: '', code: '', address: '' })

  const createCompany = useMutation({
    mutationFn: orgApi.createCompany,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      setCompanyForm({ name: '', code: '' })
    },
  })

  const createPlant = useMutation({
    mutationFn: orgApi.createPlant,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plants'] })
      setPlantForm({ company_id: '', name: '', code: '', address: '' })
    },
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Organization" description="Companies and plants under your tenant." />

      <Card
        title="Companies"
        icon={<Building2 className="h-4 w-4" />}
        actions={
          <form
            className="flex items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              createCompany.mutate(companyForm)
            }}
          >
            <Input
              placeholder="Name"
              required
              value={companyForm.name}
              onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })}
              className="w-40"
            />
            <Input
              placeholder="Code"
              required
              value={companyForm.code}
              onChange={(e) => setCompanyForm({ ...companyForm, code: e.target.value })}
              className="w-28"
            />
            <Button type="submit" disabled={createCompany.isPending}>
              Add
            </Button>
          </form>
        }
      >
        {companies.length === 0 ? (
          <EmptyState message="No companies yet. Add one above." />
        ) : (
          <Table headers={['Name', 'Code', 'Status']}>
            {companies.map((c) => (
              <tr key={c.id}>
                <td className="px-3 py-2">{c.name}</td>
                <td className="px-3 py-2 text-slate-500">{c.code}</td>
                <td className="px-3 py-2">
                  <Badge tone={c.is_active ? 'green' : 'slate'}>{c.is_active ? 'Active' : 'Inactive'}</Badge>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <Card
        title="Plants"
        icon={<Factory className="h-4 w-4" />}
        actions={
          <form
            className="flex items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              createPlant.mutate(plantForm)
            }}
          >
            <Select
              required
              value={plantForm.company_id}
              onChange={(e) => setPlantForm({ ...plantForm, company_id: e.target.value })}
              className="w-40"
            >
              <option value="">Company…</option>
              {companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
            <Input
              placeholder="Name"
              required
              value={plantForm.name}
              onChange={(e) => setPlantForm({ ...plantForm, name: e.target.value })}
              className="w-32"
            />
            <Input
              placeholder="Code"
              required
              value={plantForm.code}
              onChange={(e) => setPlantForm({ ...plantForm, code: e.target.value })}
              className="w-24"
            />
            <Button type="submit" disabled={createPlant.isPending}>
              Add
            </Button>
          </form>
        }
      >
        {plants.length === 0 ? (
          <EmptyState message="No plants yet. Add one above." />
        ) : (
          <Table headers={['Name', 'Code', 'Company', 'Status']}>
            {plants.map((p) => (
              <tr key={p.id}>
                <td className="px-3 py-2">{p.name}</td>
                <td className="px-3 py-2 text-slate-500">{p.code}</td>
                <td className="px-3 py-2 text-slate-500">
                  {companies.find((c) => c.id === p.company_id)?.name ?? '—'}
                </td>
                <td className="px-3 py-2">
                  <Badge tone={p.is_active ? 'green' : 'slate'}>{p.is_active ? 'Active' : 'Inactive'}</Badge>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </div>
  )
}
