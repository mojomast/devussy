import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AppLayout } from "@/components/layout/AppLayout";
import { ThemeProvider } from "@/components/theme/ThemeProvider";

const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Devussy",
  description: "AI-Powered Development Pipeline",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark overflow-hidden" style={{ overscrollBehavior: 'none' }}>
      <body className={`${jetbrainsMono.className} antialiased overflow-hidden h-full`} style={{ overscrollBehavior: 'none' }}>
        <ThemeProvider>
          <div className="scanlines" />
          <AppLayout>
            {children}
          </AppLayout>
        </ThemeProvider>
      </body>
    </html>
  );
}

