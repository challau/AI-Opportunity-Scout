import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/sonner";

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
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-sans antialiased">
        <Providers>
          {children}
          <Toaster richColors position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
