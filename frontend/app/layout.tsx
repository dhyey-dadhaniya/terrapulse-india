import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TerraPulse India",
  description: "TerraPulse India platform frontend",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
