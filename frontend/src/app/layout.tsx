import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";



export const metadata: Metadata = {
  title: "AI Niche Scroller",
  description: "AI related news feed",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      {/* ★ body の className から bg-gray-50 を削除し、bg-white に */}
      <body
        className={`${GeistSans.variable} ${GeistMono.variable} antialiased bg-white text-black`}
      >
        {children}
      </body>
    </html>
  );
}
