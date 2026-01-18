import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { BackgroundTaskProvider } from './contexts/BackgroundTaskContext';
import { Toaster } from 'sonner';
import AppRoutes from './routes/AppRoutes';
import GlobalFloatingProgress from './components/common/GlobalFloatingProgress';

function App() {
  return (
    <AuthProvider>
      <BackgroundTaskProvider>
        <AppRoutes />
        <Toaster position="top-right" richColors />
        <GlobalFloatingProgress />
      </BackgroundTaskProvider>
    </AuthProvider>
  );
}

export default App;
