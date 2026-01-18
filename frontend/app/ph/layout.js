'use client';

import { RecaudosProvider } from '../../contexts/RecaudosContext';

export default function PHLayout({ children }) {
    return (
        <RecaudosProvider>
            {children}
        </RecaudosProvider>
    );
}
