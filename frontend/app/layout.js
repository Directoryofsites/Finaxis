import TopNavigationBar from '../components/TopNavigationBar';
import "./globals.css";
import 'react-toastify/dist/ReactToastify.css';
import { ToastContainer } from 'react-toastify';
import { AuthProvider } from "./context/AuthContext";
import SidebarFavorites from "./components/SidebarFavorites";

export const metadata = {
  title: "Sistema Finaxis",
  description: "Sistema contable integral para Colombia",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>
        <AuthProvider>
          <TopNavigationBar />
          <SidebarFavorites />
          {children}
          <ToastContainer position="bottom-right" autoClose={3000} />
        </AuthProvider>
      </body>
    </html>
  );
}