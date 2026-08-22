import { createContext, useContext, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { orgApi } from '../api/endpoints'
import type { Plant } from '../api/types'
import { useAuth } from './AuthContext'

interface PlantContextValue {
  plants: Plant[]
  selectedPlantId: string | null
  setSelectedPlantId: (id: string | null) => void
  isLoading: boolean
}

const PlantContext = createContext<PlantContextValue | null>(null)
const STORAGE_KEY = 'metam.selected_plant_id'

export function PlantProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [explicitPlantId, setExplicitPlantId] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY))

  const { data: plants = [], isLoading } = useQuery({
    queryKey: ['plants', user?.tenant_id],
    queryFn: () => orgApi.listPlants(),
    enabled: !!user,
  })

  // Fall back to the first plant once the list loads, without an effect:
  // derive it during render rather than syncing state after the fact.
  const explicitIsValid = explicitPlantId !== null && plants.some((p) => p.id === explicitPlantId)
  const selectedPlantId = explicitIsValid ? explicitPlantId : (plants[0]?.id ?? null)

  const setSelectedPlantId = (id: string | null) => {
    setExplicitPlantId(id)
    if (id) {
      localStorage.setItem(STORAGE_KEY, id)
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  return (
    <PlantContext.Provider value={{ plants, selectedPlantId, setSelectedPlantId, isLoading }}>
      {children}
    </PlantContext.Provider>
  )
}

export function usePlant(): PlantContextValue {
  const ctx = useContext(PlantContext)
  if (!ctx) {
    throw new Error('usePlant must be used within PlantProvider')
  }
  return ctx
}
