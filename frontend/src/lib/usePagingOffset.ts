import { useState } from 'react'

/**
 * Pagination offset that resets to 0 whenever `resetKey` changes (e.g. the
 * selected plant). Adjusts state during render per React's own pattern for
 * this ("you can call the set function while rendering") rather than in a
 * useEffect, which would cost an extra render pass for no benefit here.
 */
export function usePagingOffset(resetKey: unknown) {
  const [state, setState] = useState({ resetKey, offset: 0 })

  if (state.resetKey !== resetKey) {
    setState({ resetKey, offset: 0 })
  }

  const setOffset = (offset: number) => setState({ resetKey, offset })

  return [state.offset, setOffset] as const
}
