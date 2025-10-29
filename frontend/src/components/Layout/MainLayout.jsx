import React from 'react';
import { Header } from './Header';

/**
 * Main Layout Component
 * Provides the basic page structure with header, sidebar, and main content area
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Main content to render
 * @param {React.ReactNode} props.sidebar - Optional sidebar content
 */
export const MainLayout = ({ children, sidebar }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <Header />

      {/* Main Content Area */}
      <div className="w-full px-4 py-8">
        <div className="grid lg:grid-cols-5 gap-4">
          {/* Sidebar - 1/5 width on large screens */}
          {sidebar && (
            <aside className="lg:col-span-1">
              {sidebar}
            </aside>
          )}

          {/* Main Content - 4/5 or 5/5 width depending on sidebar */}
          <main className={sidebar ? 'lg:col-span-4' : 'lg:col-span-5'}>
            {children}
          </main>
        </div>
      </div>
    </div>
  );
};
