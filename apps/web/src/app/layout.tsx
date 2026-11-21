import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dự án | FINZ SEO Assistant",
  description: "Không gian dự án SEO local — nền tảng M0 với dữ liệu demo.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
