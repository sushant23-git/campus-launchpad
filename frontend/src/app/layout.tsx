import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Campus Launchpad",
  description: "Student development, exploration, collaboration and project platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <main className="min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
