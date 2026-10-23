import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Navbar } from "@/components/navbar";
import { AuthProvider } from "@/lib/auth-context";
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
  title: "AICF — AI Content Forensics & Authenticity Intelligence Platform",
  description:
    "Detect. Analyze. Explain. Verify. Enterprise forensic intelligence across text, image, audio, and video content.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#0B0C10] text-[#F8F9FA] selection:bg-[#D4AF37] selection:text-black">
        <AuthProvider>
          <Navbar />
          <div className="flex-1 forensic-grid">{children}</div>
          <footer className="border-t border-[#2B2F3D] bg-[#0B0C10] py-6 text-center text-xs text-[#6B7280]">
            <div className="mx-auto max-w-7xl px-4 sm:px-6">
              <p>
                AICF Forensic Intelligence Platform &bull; Detect &bull; Analyze &bull; Explain &bull; Verify
              </p>
              <p className="mt-1 text-[11px] text-[#4B5563]">
                AI detection systems produce probabilistic indicators. Forensic verification outputs are not definitive guarantees.
              </p>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
