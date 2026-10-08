import { describe, expect, it } from "vitest";

describe("ShadeShift client", () => {
  it("has a stable API default", () => {
    expect(import.meta.env.VITE_API_URL ?? "http://localhost:8000").toContain("http");
  });
});
