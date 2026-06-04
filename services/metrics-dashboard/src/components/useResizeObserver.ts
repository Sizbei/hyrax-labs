/** Observe an element's content box size for responsive D3 charts. */
import { useEffect, useState, type RefObject } from "react";

export interface Size {
  width: number;
  height: number;
}

export function useResizeObserver<T extends HTMLElement>(
  ref: RefObject<T | null>,
): Size {
  const [size, setSize] = useState<Size>({ width: 0, height: 0 });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      setSize({ width, height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref]);

  return size;
}
