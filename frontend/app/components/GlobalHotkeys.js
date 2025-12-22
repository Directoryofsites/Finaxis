'use client';

import { useEffect, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';

export default function GlobalHotkeys() {
    const router = useRouter();
    const pathname = usePathname();
    const spacePressed = useRef(false);

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.code === 'Space') {
                spacePressed.current = true;
            }

            // SPACE + X
            if (spacePressed.current && (e.key === 'x' || e.key === 'X')) {
                e.preventDefault(); // Prevent typing 'x'

                // If on home, focus input
                if (pathname === '/') {
                    const input = document.getElementById('smart-search-input');
                    if (input) {
                        input.focus();
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                } else {
                    // Navigate to home with trigger
                    router.push('/?trigger=focus_search');
                }
            }
        };

        const handleKeyUp = (e) => {
            if (e.code === 'Space') {
                spacePressed.current = false;
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, [router, pathname]);

    return null;
}
