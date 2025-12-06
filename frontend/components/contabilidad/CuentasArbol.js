// components/contabilidad/CuentasArbol.js

import Link from 'next/link';

// Este es nuestro componente recursivo
const CuentaRow = ({ cuenta, nivel, onCuentaEliminada }) => {
  const handleDeleteClick = () => {
    // Esta función se pasará desde la página principal
    onCuentaEliminada(cuenta.id, cuenta.nombre);
  };

  return (
    <>
      {/* Fila para la cuenta actual */}
      <tr className="hover:bg-gray-50">
        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono" style={{ paddingLeft: `${1.5 + nivel * 1.5}rem` }}>
          {cuenta.codigo}
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm">{cuenta.nombre}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-center">{cuenta.nivel}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
            cuenta.permite_movimiento ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {cuenta.permite_movimiento ? 'Sí' : 'No'}
          </span>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">{cuenta.funcion_especial || 'N/A'}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
          <Link href={`/admin/plan-de-cuentas/editar/${cuenta.id}`} className="text-indigo-600 hover:text-indigo-900">Editar</Link>
          <button onClick={handleDeleteClick} className="ml-4 text-red-600 hover:text-red-900">
            Eliminar
          </button>
        </td>
      </tr>
      {/* Si la cuenta tiene hijos, llamamos a este mismo componente para dibujarlos */}
      {cuenta.children && cuenta.children.length > 0 && (
        <CuentasArbol cuentas={cuenta.children} nivel={nivel + 1} onCuentaEliminada={onCuentaEliminada} />
      )}
    </>
  );
};


// Componente principal que inicia el árbol
export default function CuentasArbol({ cuentas, nivel = 0, onCuentaEliminada }) {
  return (
    <>
      {cuentas.map(cuenta => (
        <CuentaRow key={cuenta.id} cuenta={cuenta} nivel={nivel} onCuentaEliminada={onCuentaEliminada} />
      ))}
    </>
  );
}