import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import { Dashboard } from './components/Dashboard'
import { StartPage } from './components/StartPage'
import { Workspace } from './components/Workspace'
import { Results } from './components/Results'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/start/:aid" element={<StartPage />} />
        <Route path="/attempt/:id" element={<Workspace />} />
        <Route path="/results/:id" element={<Results />} />
        <Route path="*" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
