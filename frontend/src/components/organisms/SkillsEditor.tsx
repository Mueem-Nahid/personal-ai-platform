"use client";

import type { Skill } from "@/lib/types";
import { Button } from "@/components/atoms/Button";
import { SkillRow } from "@/components/molecules/SkillRow";

interface SkillsEditorProps {
  skills: Skill[];
  onAdd: () => void;
  onChange: (skill: Skill, field: keyof Skill, value: string) => void;
  onDelete: (skillId: string) => void;
}

export function SkillsEditor({ skills, onAdd, onChange, onDelete }: SkillsEditorProps) {
  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Skills</h2>
        <Button variant="ghost" size="sm" onClick={onAdd}>
          + Add Skill
        </Button>
      </div>
      <div className="space-y-2">
        {skills.map((skill) => (
          <SkillRow key={skill.id} skill={skill} onChange={onChange} onDelete={onDelete} />
        ))}
        {skills.length === 0 && (
          <p className="text-sm opacity-50">No skills yet. Click &quot;Add Skill&quot; to get started.</p>
        )}
      </div>
    </div>
  );
}
