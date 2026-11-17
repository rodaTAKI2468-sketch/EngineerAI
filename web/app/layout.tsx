import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EngineerAI — Engineering, explained.",
  description:
    "Understand engineering calculations with visual analysis and step-by-step worked solutions.",
  applicationName: "EngineerAI",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en-ZA">
      <body>{children}</body>
    </html>
  );
}
