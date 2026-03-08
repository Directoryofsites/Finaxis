import React from 'react'
import CustomerPortalWidget from './components/CustomerPortalWidget'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* 
        El Portal se dibuja aquí como un Drawer fijo a la derecha ("fixed right-0").
        El botón flotante para acceder se renderiza automáticamente desde este componente.
      */}
      <CustomerPortalWidget />
    </div>
  )
}

export default App
