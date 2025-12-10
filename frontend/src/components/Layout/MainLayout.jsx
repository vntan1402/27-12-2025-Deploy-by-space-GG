/**
 * Main Layout Component
 * Provides consistent layout structure for all pages
 */
import React from 'react';
import { Header } from './Header';

export const MainLayout = ({ children, sidebar }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <Header />

      <div className="w-full px-4 py-8">
        <div className="flex gap-4">
          {/* Sidebar - 16% width (80% of original 20%) */}
          {sidebar && (
            <div className="w-[240px] flex-shrink-0">
              {sidebar}
            </div>
          )}

          {/* Main Content - flex-1 (remaining space) */}
          <div className="flex-1">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};
