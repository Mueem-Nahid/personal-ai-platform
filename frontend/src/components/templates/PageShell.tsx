"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/profile", label: "Profile" },
  { href: "/knowledge", label: "Knowledge Base" },
  { href: "/jobs", label: "Jobs" },
];

export function PageShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen">
      <nav className="border-b dark:border-gray-700">
        <div className="mx-auto flex max-w-4xl items-center gap-6 px-8 py-3">
          <Link href="/" className="text-lg font-bold">
            Career Agent
          </Link>
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm transition-colors hover:text-blue-600 ${
                pathname === link.href ? "font-medium text-blue-600" : "opacity-60"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </nav>
      <main className="mx-auto max-w-4xl p-8">{children}</main>
    </div>
  );
}
