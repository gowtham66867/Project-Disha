import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ProspectDetail from './pages/ProspectDetail'
import Copilot from './components/Copilot'

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/prospect/:id" element={<ProspectDetail />} />
      </Routes>
      <Copilot />
    </>
  )
}
