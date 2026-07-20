import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/sonner";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: {
    default: "AI Opportunity Scout",
    template: "%s | AI Opportunity Scout",
  },
  description:
    "Automatically discover hackathons, coding contests, internships, and developer events. AI-powered recommendations delivered to your inbox.",
  keywords: [
    "hackathon", "coding contest", "internship", "developer events",
    "ai recommendations", "unstop", "devfolio", "gsoc",
  ],
  authors: [{ name: "AI Opportunity Scout" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: process.env.NEXT_PUBLIC_APP_URL,
    title: "AI Opportunity Scout",
    description: "Never miss a hackathon or coding contest again.",
    siteName: "AI Opportunity Scout",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>
          {children}
          <Toaster richColors position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
