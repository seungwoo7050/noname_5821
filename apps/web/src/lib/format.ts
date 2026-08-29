import type { PublicAggregate } from "./api";

export function formatMinutes(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  if (!hours) return `${remaining}분`;
  if (!remaining) return `${hours}시간`;
  return `${hours}시간 ${remaining}분`;
}

export function scopeLabel(scope: PublicAggregate["completion_scope"]): string {
  return {
    main_story: "메인 스토리",
    main_plus_optional: "메인 + 선택 콘텐츠",
    completionist: "완전 공략",
  }[scope];
}
