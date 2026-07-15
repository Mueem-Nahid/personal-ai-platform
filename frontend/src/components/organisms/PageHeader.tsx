import Link from "next/link";

interface PageHeaderProps {
  title: string;
  backHref?: string;
  children?: React.ReactNode;
}

export function PageHeader({ title, backHref, children }: PageHeaderProps) {
  return (
    <div className="mb-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        {backHref && (
          <Link href={backHref} className="text-sm opacity-60 hover:underline">
            &larr; Back
          </Link>
        )}
        <h1 className="text-3xl font-bold">{title}</h1>
      </div>
      {children}
    </div>
  );
}
