import type { JobPost } from "@/lib/types";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";

const statusVariant: Record<string, "gray" | "green" | "red"> = {
  parsing: "gray",
  parsed: "green",
  failed: "red",
};

interface JobCardProps {
  job: JobPost;
  onView: (id: string) => void;
  onDelete: (id: string) => void;
}

export function JobCard({ job, onView, onDelete }: JobCardProps) {
  const fields = job.parsed_fields;
  const skills = fields?.skills?.slice(0, 5) ?? [];

  return (
    <div className="flex items-start justify-between rounded-lg border p-4 dark:border-gray-700">
      <div className="min-w-0 flex-1">
        <p className="font-medium truncate">
          {fields?.title || job.title || "Untitled"}
        </p>
        <p className="text-sm opacity-70">
          {fields?.company || job.company || "Unknown company"}
          {fields?.location ? ` · ${fields.location}` : ""}
        </p>
        {fields?.salary && (
          <p className="mt-1 text-xs font-medium text-green-600 dark:text-green-400">
            {fields.salary}
          </p>
        )}
        {skills.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {skills.map((s) => (
              <Badge key={s} variant="gray">{s}</Badge>
            ))}
          </div>
        )}
        <div className="mt-2 flex items-center gap-2 text-xs opacity-50">
          <span>{job.source}</span>
          <Badge variant={statusVariant[job.status] ?? "gray"}>{job.status}</Badge>
        </div>
      </div>
      <div className="ml-4 flex shrink-0 items-center gap-2">
        <Button variant="ghost" size="sm" onClick={() => onView(job.id)}>
          View
        </Button>
        <Button variant="danger" size="sm" onClick={() => onDelete(job.id)}>
          Delete
        </Button>
      </div>
    </div>
  );
}
