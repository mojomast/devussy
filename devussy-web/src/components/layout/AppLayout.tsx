import React from 'react';
import { Header } from './Header';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="relative min-h-screen bg-background font-sans text-foreground antialiased selection:bg-primary/20 selection:text-primary">
      {/* Put the background logo above the background color but below UI windows */}
      <div className="fixed inset-0 z-0 bg-logo" />
      {/* Slight radial overlay above the logo but below content */}
      <div className="fixed inset-0 z-10 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/5 via-background to-background opacity-40" />


      <Header />

      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}
