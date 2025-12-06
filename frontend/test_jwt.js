// test_jwt.js
import { jwtDecode } from 'jwt-decode';

try {
    // Un token JWT de ejemplo (no real, solo para probar la función)
    const sampleToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJlbXByZXNhX2lkIjoxMH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c";
    const decoded = jwtDecode(sampleToken);
    console.log("jwtDecode funciona. Token decodificado:", decoded);
} catch (error) {
    console.error("Error al usar jwtDecode:", error);
}