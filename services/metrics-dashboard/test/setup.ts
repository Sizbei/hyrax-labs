import "@testing-library/jest-dom/vitest";

// jsdom lacks ResizeObserver; provide a no-op so chart hosts mount in tests.
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

globalThis.ResizeObserver =
  globalThis.ResizeObserver ?? (ResizeObserverStub as unknown as typeof ResizeObserver);
