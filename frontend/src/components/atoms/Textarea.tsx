import { cn } from "./cn";

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export function Textarea({ label, className, id, ...props }: TextareaProps) {
  const textareaId = id ?? props.name;
  return (
    <div>
      {label && (
        <label htmlFor={textareaId} className="mb-1 block text-sm font-medium">
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        className={cn("w-full rounded border px-3 py-2 dark:bg-gray-800 dark:text-white", className)}
        rows={3}
        {...props}
      />
    </div>
  );
}
