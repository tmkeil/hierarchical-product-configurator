/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  // weitere env variables hier...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
