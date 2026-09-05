import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Payment Burst Sentinel — Behavioral Anomaly Intelligence",
  description:
    "Merchant-specific behavioral anomaly monitoring. Identifies unusual payment behavior against historical baselines.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
