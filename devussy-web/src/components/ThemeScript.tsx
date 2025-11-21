"use client";

import React from 'react';

const script = `
(function() {
  try {
    const theme = localStorage.getItem('devussy-web-theme') || 'dark';
    document.documentElement.className = theme.split(' ').join(' ');
  } catch (e) {
    console.error('Failed to apply theme from localStorage', e);
  }
})();
`;

export function ThemeScript() {
  return <script dangerouslySetInnerHTML={{ __html: script }} />;
}
