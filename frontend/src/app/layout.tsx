import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ResearchPilot AI",
  description: "Agentic Research Intelligence & Literature Analysis Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="antialiased">
      <body
        className={`${inter.variable} ${inter.className} min-h-screen bg-slate-50 text-slate-900 selection:bg-blue-100`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
