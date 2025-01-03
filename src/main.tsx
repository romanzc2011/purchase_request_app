import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import PurchaseRequestForm from './components/purchase_req/PurchaseRequestForm.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <PurchaseRequestForm />
  </StrictMode>,
)
