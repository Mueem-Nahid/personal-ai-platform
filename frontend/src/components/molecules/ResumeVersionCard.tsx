import type { ResumeVersion } from "@/lib/types";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";

interface ResumeVersionCardProps {
  version: ResumeVersion;
  onView: () => void;
  onDelete: () => void;
  onRender?: () => void;
}

export function ResumeVersionCard({ version, onView, onDelete, onRender }: ResumeVersionCardProps) {
  const statusVariant = version.status === "built" ? "green" : version.status === "failed" ? "red" : "yellow";

  return (
    <div className="flex items-center justify-between rounded-lg border p-3 dark:border-gray-700">
      <div className="flex items-center gap-3">
        <Badge variant="gray">v{version.version_no}</Badge>
        <Badge variant={statusVariant}>{version.status}</Badge>
        {version.provider && (
          <span className="text-xs opacity-50">{version.provider} / {version.model}</span>
        )}
        <span className="text-xs opacity-40">
          {new Date(version.created_at).toLocaleString()}
        </span>
      </div>
      <div className="flex gap-2">
        {version.status === "built" && (
          <>
            <Button variant="secondary" size="sm" onClick={onView}>
              View
            </Button>
            {onRender && (
              <Button variant="secondary" size="sm" onClick={onRender}>
                Render PDF
              </Button>
            )}
          </>
        )}
        <Button variant="ghost" size="sm" onClick={onDelete}>
          Delete
        </Button>
      </div>
    </div>
  );
}
