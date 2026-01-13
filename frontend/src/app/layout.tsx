import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEURO-SENTINEL | Autonomous Infrastructure Surgeon",
  description: "AI-powered autonomous infrastructure management with Gemini 3 Pro. Real-time code surgery through 1M token context reasoning.",
  keywords: ["AI", "DevOps", "Infrastructure", "Autonomous", "Gemini", "Machine Learning"],
  authors: [{ name: "NEURO-SENTINEL Team" }],
  openGraph: {
    title: "NEURO-SENTINEL",
    description: "The Autonomous Infrastructure Surgeon",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta name="theme-color" content="#000000" />
        <meta name="color-scheme" content="dark" />
      </head>
      <body className="antialiased">
        {/* Main content */}
        {children}
      </body>
    </html>
  );
}
