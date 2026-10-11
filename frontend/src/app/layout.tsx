import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PrintSift | Contract Analysis Portfolio Project",
  description:
    "A full-stack contract analysis project built with FastAPI, Next.js, structured AI extraction and evidence verification.",
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
