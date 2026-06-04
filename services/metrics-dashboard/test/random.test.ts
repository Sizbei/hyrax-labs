import { describe, it, expect } from "vitest";
import { createRng, hashString, randInt, randRange, pick } from "../src/data/random";

describe("seeded random utilities", () => {
  it("produces a deterministic stream for a seed", () => {
    const a = createRng(7);
    const b = createRng(7);
    expect([a(), a(), a()]).toEqual([b(), b(), b()]);
  });

  it("returns floats in [0, 1)", () => {
    const rng = createRng(99);
    for (let i = 0; i < 1000; i += 1) {
      const v = rng();
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });

  it("hashes strings stably", () => {
    expect(hashString("views")).toBe(hashString("views"));
    expect(hashString("views")).not.toBe(hashString("likes"));
  });

  it("bounds randInt and randRange", () => {
    const rng = createRng(3);
    for (let i = 0; i < 500; i += 1) {
      const n = randInt(rng, 2, 5);
      expect(n).toBeGreaterThanOrEqual(2);
      expect(n).toBeLessThanOrEqual(5);
      const f = randRange(rng, 10, 20);
      expect(f).toBeGreaterThanOrEqual(10);
      expect(f).toBeLessThan(20);
    }
  });

  it("picks an element from the array", () => {
    const rng = createRng(5);
    const items = ["a", "b", "c"] as const;
    expect(items).toContain(pick(rng, items));
  });
});
