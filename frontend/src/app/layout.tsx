import type { Metadata } from "next";
import { PageShell } from "@/components/templates/PageShell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Career Agent",
  description: "Offline personalized job-application agent",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <PageShell>{children}</PageShell>
      </body>
    </html>
  );
}
