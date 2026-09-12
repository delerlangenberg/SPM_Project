import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  ),
  title: "SPM Prusa Project — Engineering Handbook",
  description:
    "The professional project handbook for the MK4S, Arduino Mega 2560 and CR Touch scanning measurement platform.",
  openGraph: {
    title: "SPM Prusa Project — Engineering Handbook",
    description:
      "One coherent engineering record for the MK4S, Arduino Mega 2560 and CR Touch measurement platform.",
    images: [{ url: "/og.png", width: 1672, height: 941 }],
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
