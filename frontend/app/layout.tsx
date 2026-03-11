import type { Metadata } from "next";
import { Manrope } from "next/font/google";

import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin", "cyrillic"],
});

export const metadata: Metadata = {
  title: "SAP FI Copilot",
  description: "Чат-помічник для SAP FI: помилки, транзакції та how-to сценарії.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="uk">
      <body className={`${manrope.variable} antialiased`}>{children}</body>
    </html>
  );
}
