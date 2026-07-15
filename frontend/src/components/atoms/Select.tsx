import { cn } from "./cn";

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}

export function Select({ label, options, className, id, ...props }: SelectProps) {
  const selectId = id ?? props.name;
  return (
    <div>
      {label && (
        <label htmlFor={selectId} className="mb-1 block text-sm font-medium">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={cn("rounded border px-3 py-2 dark:bg-gray-800 dark:text-white", className)}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
