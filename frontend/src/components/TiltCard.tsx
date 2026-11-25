"use client";

import React from "react";

interface TiltCardProps {
  children: React.ReactNode;
  className?: string;
  maxTilt?: number;
  glare?: boolean;
  scale?: number;
}

export default function TiltCard({
  children,
  className = "",
}: TiltCardProps) {
  return (
    <div className={`transition-all duration-200 ${className}`}>
      {children}
    </div>
  );
}
