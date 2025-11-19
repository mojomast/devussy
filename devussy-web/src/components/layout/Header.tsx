import React from 'react';
import { Terminal } from 'lucide-react';

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-screen-2xl items-center">
        <div className="mr-4 flex items-center space-x-2">
          <Terminal className="h-6 w-6 text-primary" />
          <span className="hidden font-bold sm:inline-block text-lg tracking-tight">
            DEVUSSY STUDIO
          </span>
        </div>
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <div className="w-full flex-1 md:w-auto md:flex-none">
            {/* Add navigation or search here later */}
          </div>
          <nav className="flex items-center">
             {/* Add social links or user menu here */}
          </nav>
        </div>
      </div>
    </header>
  );
}
