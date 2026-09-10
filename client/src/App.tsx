import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { DashboardLayout, RootLayout } from './components/layout/DashboardLayout';
import { Dashboard } from './pages/Dashboard';
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { DocumentDetail } from './pages/DocumentDetail';

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<RootLayout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>

        <Route element={<DashboardLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/document/:fileId" element={<DocumentDetail />} />
          <Route path="/document/:fileId/preview" element={<DocumentDetail previewOnly />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
