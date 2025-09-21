import { GoogleOAuthProvider } from '@react-oauth/google'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import { StrictMode } from 'react'
import App from './App.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
        <App />
      </GoogleOAuthProvider>
    </BrowserRouter>  
  </StrictMode>,
)
