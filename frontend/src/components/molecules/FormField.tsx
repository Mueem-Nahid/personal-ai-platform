import { ReactNode } from "react";

interface FormFieldProps {
  label: string;
  children: ReactNode;
  span?: "half" | "full";
}

export function FormField({ label, children, span = "half" }: FormFieldProps) {
  return (
    <div className={span === "full" ? "col-span-2" : ""}>
      <label className="mb-1 block text-sm font-medium">{label}</label>
      {children}
    </div>
  );
}
