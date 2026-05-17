import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SecBrief — Explain the risk, enforce the fix",
  description:
    "OWASP-mapped security briefings, code audits, and ArmorIQ-verified remediation plans.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
