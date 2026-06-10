import { t } from "@/i18n";
import { describe, expect, it } from "vitest";

describe("i18n", () => {
  it("should return translation for known key", () => {
    expect(t("app.title")).toBe("NEXUS AI");
  });

  it("should return fallback for unknown key", () => {
    expect(t("unknown.key", "fallback")).toBe("fallback");
  });

  it("should return key when no fallback provided", () => {
    expect(t("unknown.key")).toBe("unknown.key");
  });
});
