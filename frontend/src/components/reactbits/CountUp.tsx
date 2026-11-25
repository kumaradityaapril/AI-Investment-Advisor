"use client";

import React, { useEffect, useRef, useState } from "react";

interface CountUpProps {
  to: number;
  from?: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  separator?: string;
  className?: string;
  delay?: number;
}

/**
 * CountUp (React Bits)
 * High-performance numerical metric counter with viewport IntersectionObserver
 * and exponential deceleration easing.
 */
export default function CountUp({
  to,
  from = 0,
  duration = 2,
  decimals = 0,
  prefix = "",
  suffix = "",
  separator = ",",
  className = "",
  delay = 0,
}: CountUpProps) {
  const [value, setValue] = useState<number>(from);
  const elementRef = useRef<HTMLSpanElement>(null);
  const hasAnimated = useRef<boolean>(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true;

          const timeoutId = setTimeout(() => {
            let startTimestamp: number | null = null;
            const diff = to - from;

            const step = (timestamp: number) => {
              if (!startTimestamp) startTimestamp = timestamp;
              const elapsed = (timestamp - startTimestamp) / 1000;
              const progress = Math.min(elapsed / duration, 1);

              // Ease Out Expo
              const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
              const current = from + diff * eased;

              setValue(current);

              if (progress < 1) {
                window.requestAnimationFrame(step);
              } else {
                setValue(to);
              }
            };

            window.requestAnimationFrame(step);
          }, delay * 1000);

          return () => clearTimeout(timeoutId);
        }
      },
      { threshold: 0.2 }
    );

    if (elementRef.current) {
      observer.observe(elementRef.current);
    }

    return () => observer.disconnect();
  }, [to, from, duration, delay]);

  const formatNumber = (val: number): string => {
    const fixed = val.toFixed(decimals);
    const [intPart, decPart] = fixed.split(".");
    const formattedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, separator);
    return decPart !== undefined ? `${formattedInt}.${decPart}` : formattedInt;
  };

  return (
    <span ref={elementRef} className={className}>
      {prefix}
      {formatNumber(value)}
      {suffix}
    </span>
  );
}
