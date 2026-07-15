type BadgeVariant = "gray" | "yellow" | "green" | "red";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
}

const variantStyles: Record<BadgeVariant, string> = {
  gray: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  yellow: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  green: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  red: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
};

export function Badge({ variant = "gray", children }: BadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${variantStyles[variant]}`}>
      {children}
    </span>
  );
}
