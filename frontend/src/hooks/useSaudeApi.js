import { useEffect, useState } from 'react'
import { obterSaude } from '../api/saude.js'

// Estados: 'carregando' | 'ok' | 'banco-indisponivel' | 'inacessivel'
export function useSaudeApi() {
  const [estado, setEstado] = useState('carregando')

  useEffect(() => {
    let ativo = true
    obterSaude().then((resultado) => {
      if (ativo) setEstado(resultado)
    })
    return () => {
      ativo = false
    }
  }, [])

  return estado
}
