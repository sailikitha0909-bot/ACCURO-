import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Accuro — CA Firm Accounting Automation",
  description: "Accurate accounts. You review, Accuro does the rest.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 font-sans text-slate-900">
        {children}
      </body>
    </html>
  );
}
