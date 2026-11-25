import { createContext, useContext } from 'react'

export const ReauthContext = createContext(null)

export function useReauth() {
  return useContext(ReauthContext)
}