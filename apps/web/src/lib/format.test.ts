import { describe, expect, it } from "vitest";

import { formatMinutes, scopeLabel } from "./format";

describe("Korean public formatting", () => {
  it("renders whole hours and remaining minutes without decimals", () => {
    expect(formatMinutes(720)).toBe("12시간");
    expect(formatMinutes(651)).toBe("10시간 51분");
    expect(formatMinutes(30)).toBe("30분");
  });

  it("labels each fixed completion scope", () => {
    expect(scopeLabel("main_story")).toBe("메인 스토리");
    expect(scopeLabel("main_plus_optional")).toBe("메인 + 선택 콘텐츠");
    expect(scopeLabel("completionist")).toBe("완전 공략");
  });
});
