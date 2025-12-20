'use client';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function RatiosPage() {
    const router = useRouter();

    useEffect(() => {
        router.replace('/analisis/dashboard');
    }, [router]);

    return <p className="p-8 text-center text-gray-500">Redirigiendo al Dashboard...</p>;
}
