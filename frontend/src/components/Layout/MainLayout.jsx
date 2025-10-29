/**
 * Main Layout Component
 * Extracted from App.js
 */
import React from 'react';
import { Header } from './Header';

export const MainLayout = ({ children, sidebar }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <Header />

      <div className="w-full px-4 py-8">
        <div className="grid lg:grid-cols-5 gap-4">
          {/* Sidebar - 1/5 width */}
          {sidebar && (
            <div className="lg:col-span-1">
              {sidebar}
            </div>
          )}

          {/* Main Content - 4/5 width */}
          <div className={sidebar ? 'lg:col-span-4' : 'lg:col-span-5'}>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};
