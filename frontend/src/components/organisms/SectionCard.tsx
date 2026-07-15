interface SectionCardProps {
  title: string;
  children: React.ReactNode;
}

export function SectionCard({ title, children }: SectionCardProps) {
  return (
    <section className="rounded-lg border p-6 dark:border-gray-700">
      {title && <h2 className="mb-4 text-xl font-semibold">{title}</h2>}
      {children}
    </section>
  );
}
