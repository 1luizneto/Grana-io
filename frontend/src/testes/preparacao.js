// Preparação comum dos testes da interface (vite.config.js → test.setupFiles).
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { _reiniciarParaTestes } from '../api/client.js'

afterEach(() => {
  cleanup()
  localStorage.clear()
  vi.unstubAllGlobals()
  _reiniciarParaTestes()
})
