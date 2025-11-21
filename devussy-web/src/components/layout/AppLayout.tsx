import React from 'react';
import { Header } from './Header';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="relative min-h-screen bg-background font-sans text-foreground antialiased selection:bg-primary/20 selection:text-primary">
      <div className="fixed inset-0 z-[-2] bg-logo" />
      <div className="fixed inset-0 z-[-1] bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/5 via-background to-background opacity-40" />


      <Header />

      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}
