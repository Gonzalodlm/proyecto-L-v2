import React from 'react';
import { Navbar } from './Navbar';

interface LayoutProps {
  children: React.ReactNode;
  showNavbar?: boolean;
}

export function Layout({ children, showNavbar = true }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      {showNavbar && <Navbar />}
      
      <main className={showNavbar ? 'pt-0' : ''}>
        {children}
      </main>
      
      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-sm text-gray-600">
              © 2024 Impulso Inversor. Todos los derechos reservados.
            </p>
            <p className="text-xs text-gray-500 mt-1">
              ⚠️ Esta aplicación es solo para fines educativos y de demostración.
              No constituye asesoramiento financiero profesional.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}