// frontend/app/components/GaugeChart.js (NUEVO ARCHIVO)
import React from 'react';

const GaugeChart = ({ title, value, max, unit, goodRange, colorClass }) => {
  const percentage = (value / max) * 100;
  // Aseguramos que el porcentaje esté entre 0 y 100
  const clampedPercentage = Math.min(Math.max(percentage, 0), 100);
  const rotation = (clampedPercentage / 100) * 180 - 90; // Rango de 180 grados (de -90 a 90)

  // Color de la aguja (ejemplo: verde si > 50%, rojo si < 25%)
  let needleColor = "bg-gray-500";
  if (value >= (max * 0.75)) {
    needleColor = "bg-green-500";
  } else if (value <= (max * 0.25)) {
    needleColor = "bg-red-500";
  } else {
    needleColor = "bg-blue-500"; // Color por defecto
  }

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-white rounded-xl shadow border border-gray-200 min-h-[180px]">
      <p className="text-sm font-medium text-gray-600 text-center mb-2">{title}</p>
      
      <div className="relative w-32 h-16 overflow-hidden">
        {/* Fondo del medidor */}
        <div className="absolute top-0 left-0 w-full h-full rounded-b-full bg-gray-200"></div>
        <div className="absolute top-0 left-0 w-full h-full rounded-b-full bg-gradient-to-r from-green-300 via-yellow-300 to-red-300 opacity-60"></div>
        
        {/* Aguja del medidor */}
        <div 
          className="absolute origin-bottom-center transition-transform duration-700 ease-out"
          style={{
            transform: `translateX(-50%) rotate(${rotation}deg)`,
            left: '50%',
            bottom: '0',
            width: '2px',
            height: 'calc(100% + 5px)', // Un poco más larga
            backgroundColor: needleColor,
            zIndex: 10,
          }}
        ></div>
        
        {/* Centro del pivote */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-4 bg-gray-700 rounded-full z-20"></div>
        
        {/* Texto de valor */}
        <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 text-xs text-gray-700 font-bold z-30">
          0 {unit}
        </div>
        <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/2 text-xs text-gray-700 font-bold z-30">
          {max}{unit}
        </div>
      </div>
      
      <p className={`text-2xl font-bold mt-4 ${colorClass}`}>{value.toFixed(2)} {unit}</p>
      <p className="text-xs text-gray-500 mt-1">Meta: {goodRange}</p>
    </div>
  );
};

export default GaugeChart;