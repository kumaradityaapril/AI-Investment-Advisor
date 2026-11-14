"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function ThreeDHeroSphere() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    // Dimensions
    const width = mount.clientWidth || 450;
    const height = mount.clientHeight || 450;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.z = 4.2;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    // Group to hold all geometries
    const group = new THREE.Group();
    scene.add(group);

    // 1. Central Core Sphere - Icosahedron with Wireframe & Glow
    const coreGeo = new THREE.IcosahedronGeometry(1.4, 2);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x4338ca,
      wireframe: true,
      roughness: 0.2,
      metalness: 0.8,
      emissive: 0x2a14b4,
      emissiveIntensity: 0.4,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    group.add(coreMesh);

    // 2. Inner Solid Nucleus
    const innerGeo = new THREE.SphereGeometry(0.85, 32, 32);
    const innerMat = new THREE.MeshStandardMaterial({
      color: 0x6063ee,
      roughness: 0.1,
      metalness: 0.9,
      emissive: 0x10b981,
      emissiveIntensity: 0.2,
    });
    const innerMesh = new THREE.Mesh(innerGeo, innerMat);
    group.add(innerMesh);

    // 3. Orbital Ring 1 - Emerald Wealth Growth
    const ringGeo1 = new THREE.TorusGeometry(2.1, 0.02, 16, 100);
    const ringMat1 = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      transparent: true,
      opacity: 0.8,
    });
    const ring1 = new THREE.Mesh(ringGeo1, ringMat1);
    ring1.rotation.x = Math.PI / 3;
    ring1.rotation.y = Math.PI / 6;
    group.add(ring1);

    // 4. Orbital Ring 2 - Electric Violet Intelligence
    const ringGeo2 = new THREE.TorusGeometry(2.3, 0.015, 16, 100);
    const ringMat2 = new THREE.MeshBasicMaterial({
      color: 0x6366f1,
      transparent: true,
      opacity: 0.6,
    });
    const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
    ring2.rotation.x = -Math.PI / 4;
    ring2.rotation.y = -Math.PI / 4;
    group.add(ring2);

    // 5. Surrounding Particle Cloud (Simulating Data Nodes)
    const particleCount = 200;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i += 3) {
      const radius = 2.4 + Math.random() * 1.2;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      positions[i] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i + 2] = radius * Math.cos(phi);
    }

    particleGeo.setAttribute(
      "position",
      new THREE.BufferAttribute(positions, 3)
    );
    const particleMat = new THREE.PointsMaterial({
      color: 0x85f8c4,
      size: 0.045,
      transparent: true,
      opacity: 0.85,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    group.add(particles);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x4338ca, 3, 50);
    pointLight1.position.set(5, 5, 5);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x10b981, 2, 50);
    pointLight2.position.set(-5, -5, 5);
    scene.add(pointLight2);

    // Mouse Interaction
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const handleMouseMove = (event: MouseEvent) => {
      const rect = mount.getBoundingClientRect();
      const x = event.clientX - rect.left - width / 2;
      const y = event.clientY - rect.top - height / 2;
      mouseX = x * 0.002;
      mouseY = y * 0.002;
    };

    window.addEventListener("mousemove", handleMouseMove);

    // Animation Loop
    let animationFrameId: number;
    const startTime = performance.now();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = (performance.now() - startTime) * 0.001;

      // Smooth mouse follow
      targetX += (mouseX - targetX) * 0.05;
      targetY += (mouseY - targetY) * 0.05;

      // Rotations
      coreMesh.rotation.y = elapsedTime * 0.3 + targetX;
      coreMesh.rotation.x = elapsedTime * 0.15 + targetY;

      innerMesh.rotation.y = -elapsedTime * 0.4;

      ring1.rotation.z = elapsedTime * 0.2;
      ring2.rotation.z = -elapsedTime * 0.25;

      particles.rotation.y = elapsedTime * 0.05 + targetX * 0.5;

      renderer.render(scene, camera);
    };

    animate();

    // Resize Handler
    const handleResize = () => {
      if (!mount) return;
      const newW = mount.clientWidth;
      const newH = mount.clientHeight;
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      if (mount.contains(renderer.domElement)) {
        mount.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  return (
    <div className="relative w-full h-[400px] sm:h-[480px] lg:h-[520px] flex items-center justify-center">
      {/* Ambient background glows */}
      <div className="absolute w-72 h-72 rounded-full bg-indigo-500/15 blur-3xl pointer-events-none"></div>
      <div className="absolute w-60 h-60 rounded-full bg-emerald-400/10 blur-2xl pointer-events-none translate-x-12 translate-y-12"></div>
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
    </div>
  );
}

