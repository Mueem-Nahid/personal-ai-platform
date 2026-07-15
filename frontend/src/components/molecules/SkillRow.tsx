import type { Skill } from "@/lib/types";
import { Button } from "@/components/atoms/Button";
import { Select } from "@/components/atoms/Select";

interface SkillRowProps {
  skill: Skill;
  onChange: (skill: Skill, field: keyof Skill, value: string) => void;
  onDelete: (skillId: string) => void;
}

const proficiencyOptions = [
  { value: "", label: "Proficiency" },
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
  { value: "expert", label: "Expert" },
];

export function SkillRow({ skill, onChange, onDelete }: SkillRowProps) {
  return (
    <div className="flex items-center gap-2">
      <input
        className="flex-1 rounded border px-2 py-1 text-sm dark:bg-gray-800 dark:text-white"
        value={skill.name}
        onChange={(e) => onChange(skill, "name", e.target.value)}
        placeholder="Skill name"
      />
      <input
        className="w-32 rounded border px-2 py-1 text-sm dark:bg-gray-800 dark:text-white"
        placeholder="Category"
        value={skill.category ?? ""}
        onChange={(e) => onChange(skill, "category", e.target.value)}
      />
      <Select
        options={proficiencyOptions}
        value={skill.proficiency ?? ""}
        onChange={(e) => onChange(skill, "proficiency", e.target.value)}
      />
      <Button variant="danger" size="sm" onClick={() => skill.id && onDelete(skill.id)}>
        Delete
      </Button>
    </div>
  );
}
