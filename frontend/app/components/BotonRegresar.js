'use client';

import Link from 'next/link';
import { FaArrowLeft } from 'react-icons/fa';

export default function BotonRegresar({ href }) {
  return (
    <div className="mb-6">
      <Link
        href={href || "/"}
        className="
            inline-flex items-center gap-2 px-5 py-2.5 
            bg-white border border-gray-200 rounded-xl shadow-sm 
            text-sm font-bold text-gray-600 
            hover:text-indigo-600 hover:border-indigo-200 hover:shadow-md 
            transition-all duration-200 transform hover:-translate-x-1
        "
      >
        <FaArrowLeft />
        <span>Regresar al Panel Principal</span>
      </Link>
    </div>
  );
}