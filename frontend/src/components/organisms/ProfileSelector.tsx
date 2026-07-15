"use client";

import type { Profile } from "@/lib/types";
import { Button } from "@/components/atoms/Button";

interface ProfileSelectorProps {
  profiles: Profile[];
  selectedId: string;
  onSelect: (profile: Profile) => void;
  onCreate: () => void;
}

export function ProfileSelector({ profiles, selectedId, onSelect, onCreate }: ProfileSelectorProps) {
  return (
    <div className="flex items-center gap-4">
      <select
        className="rounded border px-3 py-2 dark:bg-gray-800 dark:text-white"
        value={selectedId}
        onChange={(e) => {
          const p = profiles.find((p) => p.id === e.target.value);
          if (p) onSelect(p);
        }}
      >
        {profiles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.full_name} {p.title ? `\u2014 ${p.title}` : ""}
          </option>
        ))}
      </select>
      <Button variant="primary" size="md" onClick={onCreate}>
        + New Profile
      </Button>
    </div>
  );
}
