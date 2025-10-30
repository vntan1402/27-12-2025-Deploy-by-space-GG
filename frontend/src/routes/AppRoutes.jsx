import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Pages
import LoginPage from '../pages/LoginPage';
import HomePage from '../pages/HomePage';
import ClassAndFlagCert from '../pages/ClassAndFlagCert';
import ClassSurveyReport from '../pages/ClassSurveyReport';
import TestReport from '../pages/TestReport';
import DrawingsManuals from '../pages/DrawingsManuals';
import OtherDocuments from '../pages/OtherDocuments';
import SystemSettingsPage from '../pages/SystemSettingsPage';

// Loading component
const LoadingScreen = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
);

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingScreen />;
  }
  
  return user ? children : <Navigate to="/login" replace />;
};

const AppRoutes = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <HomePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/certificates"
          element={
            <ProtectedRoute>
              <ClassAndFlagCert />
            </ProtectedRoute>
          }
        />
        <Route
          path="/class-survey-report"
          element={
            <ProtectedRoute>
              <ClassSurveyReport />
            </ProtectedRoute>
          }
        />
        <Route
          path="/test-report"
          element={
            <ProtectedRoute>
              <TestReport />
            </ProtectedRoute>
          }
        />
        <Route
          path="/drawings-manuals"
          element={
            <ProtectedRoute>
              <DrawingsManuals />
            </ProtectedRoute>
          }
        />
        <Route
          path="/other-documents"
          element={
            <ProtectedRoute>
              <OtherDocuments />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <SystemSettingsPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRoutes;
