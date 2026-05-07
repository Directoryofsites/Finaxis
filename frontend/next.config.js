/** @type {import('next').NextConfig} */
const nextConfig = {
  // Para la versión WEB (Vercel/servidor): dejar esto sin cambios.
  // Para el INSTALADOR LOCAL: el script build_instalador.bat activa
  // la variable NEXT_PUBLIC_API_URL=http://localhost:8765 antes de compilar,
  // lo cual es suficiente para que el frontend apunte al backend local.

  // Si en el futuro se necesita export estático (carpeta 'out'),
  // descomentar la siguiente línea:
  output: 'standalone',

  // Permitir imágenes de cualquier origen (útil para logos de empresa)
  images: {
    unoptimized: true,  // Necesario para export estático
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
      }
    ],
  },

  // Ignorar errores de TypeScript/ESLint en el build del instalador
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
