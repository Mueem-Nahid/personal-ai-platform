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
    <div className="min-w-0 space-y-3 rounded-lg border p-3 dark:border-gray-700">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="gray">v{version.version_no}</Badge>
        <Badge variant={statusVariant}>{version.status}</Badge>
      </div>
      <div className="min-w-0 space-y-1">
        {version.provider && (
          <p className="text-xs opacity-50 [overflow-wrap:anywhere]">{version.provider} / {version.model}</p>
        )}
        <time dateTime={version.created_at} className="block text-xs opacity-40">
          {new Date(version.created_at).toLocaleString()}
        </time>
      </div>
      <div className="flex flex-wrap gap-2 border-t pt-3 dark:border-gray-700">
        {version.status === "built" && (
          <>
            <Button variant="secondary" size="sm" className="shrink-0 whitespace-nowrap px-2.5" onClick={onView}>
              View
            </Button>
            {onRender && (
              <Button variant="secondary" size="sm" className="shrink-0 whitespace-nowrap px-2.5" onClick={onRender}>
                Render PDF
              </Button>
            )}
          </>
        )}
        <Button variant="ghost" size="sm" className="shrink-0 whitespace-nowrap px-2.5" onClick={onDelete}>
          Delete
        </Button>
      </div>
    </div>
  );
}
