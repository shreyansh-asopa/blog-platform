import { useQuery } from '@tanstack/react-query'
import { topicsApi } from './endpoints'

/** The topic list, shared by the sidebar, search and the editor. It rarely changes. */
export function useTopics() {
  return useQuery({
    queryKey: ['topics'],
    queryFn: topicsApi.list,
    staleTime: 5 * 60_000,
  })
}
