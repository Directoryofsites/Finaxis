import "./globals.css";
import 'react-toastify/dist/ReactToastify.css';
import { ToastContainer } from 'react-toastify';
import { AuthProvider } from "./context/AuthContext";
import SmartLayout from "./components/SmartLayout";
import GlobalHotkeys from "./components/GlobalHotkeys";
import { DM_Sans, IBM_Plex_Sans } from 'next/font/google';

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-dm-sans',
  display: 'swap',
});

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-ibm-plex-sans',
  display: 'swap',
});

export const metadata = {
  title: "Sistema Finaxis",
  description: "Sistema contable integral para Colombia",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es" className={`${dmSans.variable} ${ibmPlexSans.variable}`}>
      <body>
        <AuthProvider>
          <SmartLayout>
            <GlobalHotkeys />
            {children}
          </SmartLayout>
          <ToastContainer position="bottom-right" autoClose={3000} />
        </AuthProvider>
      </body>
    </html>
  );
}