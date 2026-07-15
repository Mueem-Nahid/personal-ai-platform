"use client";

import type { Profile } from "@/lib/types";
import { FormField } from "@/components/molecules/FormField";
import { Input } from "@/components/atoms/Input";
import { Textarea } from "@/components/atoms/Textarea";

interface BasicInfoFormProps {
  profile: Profile;
  onChange: (field: keyof Profile, value: string) => void;
}

export function BasicInfoForm({ profile, onChange }: BasicInfoFormProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <FormField label="Full Name">
        <Input value={profile.full_name ?? ""} onChange={(e) => onChange("full_name", e.target.value)} />
      </FormField>
      <FormField label="Title">
        <Input value={profile.title ?? ""} onChange={(e) => onChange("title", e.target.value)} />
      </FormField>
      <FormField label="Email">
        <Input value={profile.email ?? ""} onChange={(e) => onChange("email", e.target.value)} />
      </FormField>
      <FormField label="Phone">
        <Input value={profile.phone ?? ""} onChange={(e) => onChange("phone", e.target.value)} />
      </FormField>
      <FormField label="Location">
        <Input value={profile.location ?? ""} onChange={(e) => onChange("location", e.target.value)} />
      </FormField>
      <FormField label="Website">
        <Input value={profile.website ?? ""} onChange={(e) => onChange("website", e.target.value)} />
      </FormField>
      <FormField label="GitHub URL">
        <Input value={profile.github_url ?? ""} onChange={(e) => onChange("github_url", e.target.value)} />
      </FormField>
      <FormField label="LinkedIn URL">
        <Input value={profile.linkedin_url ?? ""} onChange={(e) => onChange("linkedin_url", e.target.value)} />
      </FormField>
      <FormField label="Summary" span="full">
        <Textarea value={profile.summary ?? ""} onChange={(e) => onChange("summary", e.target.value)} />
      </FormField>
    </div>
  );
}
