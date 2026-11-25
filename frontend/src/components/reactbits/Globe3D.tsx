"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface Globe3DProps {
  className?: string;
  size?: number;
}

/**
 * Globe3D (React Bits 3D Interactive Component)
 * Powered by Three.js. Renders an interactive 3D financial earth sphere with
 * latitude/longitude grid rings, global capital market hubs (NSE, NYSE, LSE),
 * and dynamic animated capital flow arcs.
 */
export default function Globe3D({ className = "w-full h-full", size = 420 }: Globe3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || size;
    const height = container.clientHeight || size;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 240;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Group for globe and all attached elements
    const globeGroup = new THREE.Group();
    scene.add(globeGroup);

    const radius = 68;

    // 1. Dotted Globe Mesh (Sphere Points)
    const pointsGeometry = new THREE.BufferGeometry();
    const pointPositions: number[] = [];
    const latCount = 32;
    const lonCount = 64;

    for (let i = 0; i <= latCount; i++) {
      const lat = (i / latCount) * Math.PI - Math.PI / 2;
      for (let j = 0; j < lonCount; j++) {
        const lon = (j / lonCount) * 2 * Math.PI;

        const x = radius * Math.cos(lat) * Math.cos(lon);
        const y = radius * Math.sin(lat);
        const z = radius * Math.cos(lat) * Math.sin(lon);

        // Density modulation for continents
        if (Math.sin(lat * 3) + Math.cos(lon * 4) > -0.4) {
          pointPositions.push(x, y, z);
        }
      }
    }

    pointsGeometry.setAttribute("position", new THREE.Float32BufferAttribute(pointPositions, 3));
    const pointsMaterial = new THREE.PointsMaterial({
      color: 0x4338ca, // Indigo-600
      size: 1.6,
      transparent: true,
      opacity: 0.65,
    });
    const globePoints = new THREE.Points(pointsGeometry, pointsMaterial);
    globeGroup.add(globePoints);

    // 2. Latitude and Longitude Rings
    const ringMaterial = new THREE.LineBasicMaterial({
      color: 0x2a14b4,
      transparent: true,
      opacity: 0.18,
    });

    for (let r = -2; r <= 2; r++) {
      const ringLat = (r * Math.PI) / 6;
      const ringRadius = radius * Math.cos(ringLat);
      const ringY = radius * Math.sin(ringLat);

      const circleGeom = new THREE.BufferGeometry();
      const circlePoints = [];
      for (let theta = 0; theta <= 64; theta++) {
        const angle = (theta / 64) * 2 * Math.PI;
        circlePoints.push(ringRadius * Math.cos(angle), ringY, ringRadius * Math.sin(angle));
      }
      circleGeom.setAttribute("position", new THREE.Float32BufferAttribute(circlePoints, 3));
      const ringLine = new THREE.Line(circleGeom, ringMaterial);
      globeGroup.add(ringLine);
    }

    // 3. Financial Hubs (Latitude, Longitude in degrees)
    const hubs = [
      { name: "Mumbai (NSE/BSE)", lat: 19.076, lon: 72.8777, color: 0x10b981 }, // Emerald
      { name: "New York (NYSE/NASDAQ)", lat: 40.7128, lon: -74.006, color: 0x2a14b4 }, // Deep Indigo
      { name: "London (LSE)", lat: 51.5074, lon: -0.1278, color: 0x0ea5e9 }, // Sky
      { name: "Singapore (SGX)", lat: 1.3521, lon: 103.8198, color: 0x10b981 }, // Emerald
      { name: "Tokyo (TSE)", lat: 35.6762, lon: 139.6503, color: 0x6366f1 }, // Indigo
    ];

    function latLonToVector3(lat: number, lon: number, r: number) {
      const phi = (90 - lat) * (Math.PI / 180);
      const theta = (lon + 180) * (Math.PI / 180);
      const x = -(r * Math.sin(phi) * Math.cos(theta));
      const z = r * Math.sin(phi) * Math.sin(theta);
      const y = r * Math.cos(phi);
      return new THREE.Vector3(x, y, z);
    }

    // Add glowing markers at hubs
    hubs.forEach((hub) => {
      const pos = latLonToVector3(hub.lat, hub.lon, radius + 1);

      const markerGeom = new THREE.SphereGeometry(2.2, 16, 16);
      const markerMat = new THREE.MeshBasicMaterial({ color: hub.color });
      const marker = new THREE.Mesh(markerGeom, markerMat);
      marker.position.copy(pos);
      globeGroup.add(marker);

      // Pulse ring around hub
      const haloGeom = new THREE.RingGeometry(2.8, 4.2, 24);
      const haloMat = new THREE.MeshBasicMaterial({
        color: hub.color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.5,
      });
      const halo = new THREE.Mesh(haloGeom, haloMat);
      halo.position.copy(pos);
      halo.lookAt(new THREE.Vector3(0, 0, 0));
      globeGroup.add(halo);
    });

    // 4. Capital Flow Arcs Connecting Hubs
    const arcPairs = [
      [0, 1], // Mumbai <-> NY
      [0, 2], // Mumbai <-> London
      [0, 3], // Mumbai <-> Singapore
      [1, 2], // NY <-> London
      [3, 4], // Singapore <-> Tokyo
    ];

    interface PulsePacket {
      curve: THREE.CubicBezierCurve3;
      mesh: THREE.Mesh;
      t: number;
      speed: number;
    }
    const packets: PulsePacket[] = [];

    arcPairs.forEach(([fromIdx, toIdx], pairIdx) => {
      const p1 = latLonToVector3(hubs[fromIdx].lat, hubs[fromIdx].lon, radius);
      const p2 = latLonToVector3(hubs[toIdx].lat, hubs[toIdx].lon, radius);

      // Control points for elevated arc
      const mid = p1.clone().add(p2).multiplyScalar(0.5);
      const distance = p1.distanceTo(p2);
      mid.normalize().multiplyScalar(radius + distance * 0.42);

      const curve = new THREE.CubicBezierCurve3(p1, mid, mid, p2);
      const curvePoints = curve.getPoints(50);
      const curveGeom = new THREE.BufferGeometry().setFromPoints(curvePoints);
      const curveMat = new THREE.LineBasicMaterial({
        color: pairIdx % 2 === 0 ? 0x10b981 : 0x4338ca,
        transparent: true,
        opacity: 0.35,
      });
      const arcLine = new THREE.Line(curveGeom, curveMat);
      globeGroup.add(arcLine);

      // Animated signal packet along arc
      const packetGeom = new THREE.SphereGeometry(1.8, 12, 12);
      const packetMat = new THREE.MeshBasicMaterial({
        color: pairIdx % 2 === 0 ? 0x85f8c4 : 0xa5b4fc,
      });
      const packetMesh = new THREE.Mesh(packetGeom, packetMat);
      globeGroup.add(packetMesh);

      packets.push({
        curve,
        mesh: packetMesh,
        t: Math.random(),
        speed: 0.006 + Math.random() * 0.004,
      });
    });

    // Interactive pointer drag rotation
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let targetRotationY = 0.5;
    let targetRotationX = 0.25;

    const onPointerDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onPointerMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;

      targetRotationY += deltaX * 0.005;
      targetRotationX += deltaY * 0.005;

      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onPointerUp = () => {
      isDragging = false;
    };

    const domEl = renderer.domElement;
    domEl.style.cursor = "grab";
    domEl.addEventListener("mousedown", onPointerDown);
    window.addEventListener("mousemove", onPointerMove);
    window.addEventListener("mouseup", onPointerUp);

    // Resize handler
    const handleResize = () => {
      if (!container) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };
    window.addEventListener("resize", handleResize);

    // Animation Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);

      // Auto-rotation when not actively dragged
      if (!isDragging) {
        targetRotationY += 0.003;
      }

      // Smooth damping interpolation
      globeGroup.rotation.y += (targetRotationY - globeGroup.rotation.y) * 0.08;
      globeGroup.rotation.x += (targetRotationX - globeGroup.rotation.x) * 0.08;

      // Restrict pitch
      targetRotationX = Math.max(-0.6, Math.min(0.6, targetRotationX));

      // Advance capital flow pulse packets
      packets.forEach((p) => {
        p.t += p.speed;
        if (p.t > 1) p.t = 0;
        const newPos = p.curve.getPoint(p.t);
        p.mesh.position.copy(newPos);
      });

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
      domEl.removeEventListener("mousedown", onPointerDown);
      window.removeEventListener("mousemove", onPointerMove);
      window.removeEventListener("mouseup", onPointerUp);

      if (container && domEl.parentNode === container) {
        container.removeChild(domEl);
      }
      renderer.dispose();
      pointsGeometry.dispose();
      pointsMaterial.dispose();
    };
  }, [size]);

  return (
    <div
      ref={mountRef}
      className={`relative flex items-center justify-center overflow-hidden ${className}`}
    />
  );
}
