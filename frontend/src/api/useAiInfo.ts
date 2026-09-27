import { useQuery } from '@tanstack/react-query'
import { aiApi } from './endpoints'

/** Whether the AI can answer. Shared by the editor, which hides the AI button when it's off */
export function useAiInfo() {
  return useQuery({ queryKey: ['ai', 'status'], queryFn: aiApi.status, staleTime: 30_000 })
}
