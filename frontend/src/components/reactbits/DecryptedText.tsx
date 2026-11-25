"use client";

import React, { useEffect, useRef, useState } from "react";

interface DecryptedTextProps {
  text: string;
  speed?: number;
  maxIterations?: number;
  sequential?: boolean;
  revealDirection?: "start" | "end" | "center";
  useOriginalCharsOnly?: boolean;
  characters?: string;
  className?: string;
  encryptedClassName?: string;
  parentClassName?: string;
  animateOn?: "view" | "hover";
}

/**
 * DecryptedText (React Bits)
 * Cryptographic / quantitative text scrambler reveal component.
 */
export default function DecryptedText({
  text,
  speed = 40,
  maxIterations = 10,
  sequential = true,
  characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_#%&$",
  className = "",
  encryptedClassName = "text-indigo-400 font-mono",
  parentClassName = "inline-block",
  animateOn = "view",
}: DecryptedTextProps) {
  const [displayText, setDisplayText] = useState<string>(text);
  const [isHovering, setIsHovering] = useState<boolean>(false);
  const [isScrambling, setIsScrambling] = useState<boolean>(false);
  const [revealedIndices, setRevealedIndices] = useState<Set<number>>(new Set());
  const containerRef = useRef<HTMLSpanElement>(null);
  const hasAnimatedRef = useRef<boolean>(false);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    let currentIteration = 0;

    const startAnimation = () => {
      setIsScrambling(true);
      currentIteration = 0;
      setRevealedIndices(new Set());

      interval = setInterval(() => {
        setDisplayText(() => {
          return text
            .split("")
            .map((char, index) => {
              if (char === " " || char === "•" || char === "&" || char === ";") return char;

              if (sequential) {
                if (revealedIndices.has(index)) return char;
                if (currentIteration > index * 1.5) {
                  setRevealedIndices((prev) => new Set(prev).add(index));
                  return char;
                }
              } else {
                if (currentIteration >= maxIterations) return char;
              }

              const randomChar = characters[Math.floor(Math.random() * characters.length)];
              return randomChar;
            })
            .join("");
        });

        currentIteration++;
        if (currentIteration > (sequential ? text.length * 2 : maxIterations)) {
          clearInterval(interval);
          setIsScrambling(false);
          setDisplayText(text);
        }
      }, speed);
    };

    if (animateOn === "view") {
      const observer = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting && !hasAnimatedRef.current) {
            hasAnimatedRef.current = true;
            startAnimation();
          }
        },
        { threshold: 0.3 }
      );

      if (containerRef.current) observer.observe(containerRef.current);
      return () => {
        observer.disconnect();
        clearInterval(interval);
      };
    } else if (animateOn === "hover" && isHovering) {
      startAnimation();
      return () => clearInterval(interval);
    }
  }, [animateOn, isHovering, maxIterations, sequential, speed, text, characters]);

  return (
    <span
      ref={containerRef}
      className={parentClassName}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <span className={isScrambling ? encryptedClassName : className}>
        {displayText}
      </span>
    </span>
  );
}
