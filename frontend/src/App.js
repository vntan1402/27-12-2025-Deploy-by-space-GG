import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { Toaster } from 'sonner';
import AppRoutes from './routes/AppRoutes';

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
      <Toaster position="top-right" richColors />
    </AuthProvider>
  );
}

export default App;
