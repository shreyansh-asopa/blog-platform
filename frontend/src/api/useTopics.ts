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

/** The sidebar's top few topics. Refreshed now and then, as likes and comments come in. */
export function useTrendingTopics(limit = 3) {
  return useQuery({
    queryKey: ['topics', 'trending', limit],
    queryFn: () => topicsApi.trending(limit),
    staleTime: 5 * 60_000,
  })
}
