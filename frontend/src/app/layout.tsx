import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/ui/Navigation";
import { WebSocketProvider } from "@/components/providers/WebSocketProvider";
import { NotificationsProvider } from "@/components/providers/NotificationsProvider";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { AppInitializer } from "@/components/providers/AppInitializer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AlphaMind Trading Platform",
  description: "AI-powered trading platform with real-time market data",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover, minimum-scale=1" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="AlphaMind" />
        <meta name="theme-color" content="#0f172a" />
        <meta name="mobile-web-app-capable" content="yes" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased overflow-x-hidden bg-gray-50`}
      >
        <ErrorBoundary>
          <AppInitializer>
            <WebSocketProvider>
              <NotificationsProvider>
                <div className="flex flex-col h-screen">
                  <Navigation />
                  <main className="flex-1 overflow-y-auto w-full px-3 sm:px-4 md:px-6 py-4 sm:py-6 md:py-8 md:container md:mx-auto pb-28 md:pb-24">
                    {children}
                  </main>
                </div>
              </NotificationsProvider>
            </WebSocketProvider>
          </AppInitializer>
        </ErrorBoundary>
      </body>
    </html>
  );
}
