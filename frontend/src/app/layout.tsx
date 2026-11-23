import type { Metadata } from "next";
import { Navbar } from "@/components/navbar";
import { AuthProvider } from "@/lib/auth-context";
import "./globals.css";

const geistSans = { variable: "font-sans" };
const geistMono = { variable: "font-mono" };

export const metadata: Metadata = {
  title: "A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media",
  description:
    "Detect. Analyze. Explain. Verify. A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media across text, image, and video content.",
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
      <body className="font-sans min-h-full flex flex-col bg-[#090A0D] text-[#F5F5F2] selection:bg-[#D6B15E] selection:text-[#090A0D]">
        <AuthProvider>
          <Navbar />
          <div className="flex-1 forensic-grid flex flex-col">{children}</div>
        </AuthProvider>
      </body>
    </html>
  );
}
