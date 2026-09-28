import { useQuery } from '@tanstack/react-query'
import { writingApi } from './endpoints'

/** Which writing checks the server can run; only changes when the server is set up */
export function useWritingStatus() {
  return useQuery({
    queryKey: ['writing', 'status'],
    queryFn: writingApi.status,
    staleTime: 60_000,
  })
}
