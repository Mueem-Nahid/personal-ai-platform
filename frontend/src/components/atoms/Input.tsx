import { cn } from "./cn";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function Input({ label, className, id, ...props }: InputProps) {
  const inputId = id ?? props.name;
  return (
    <div>
      {label && (
        <label htmlFor={inputId} className="mb-1 block text-sm font-medium">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={cn("w-full rounded border px-3 py-2 dark:bg-gray-800 dark:text-white", className)}
        {...props}
      />
    </div>
  );
}
