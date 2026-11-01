import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export const VoxelFloorCanvas: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    let renderer: THREE.WebGLRenderer | null = null;
    try {
      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
      if (!gl) return;

      renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance',
      });
    } catch {
      return;
    }
    if (!renderer) return;

    const scene = new THREE.Scene();

    // Pale lavender horizon fog blending seamlessly into sky gradient (#E6DDF8)
    scene.fog = new THREE.Fog(0xe6ddf8, 12, 28);

    const camera = new THREE.PerspectiveCamera(
      42,
      container.clientWidth / container.clientHeight,
      0.1,
      60
    );
    // Perspective camera viewing the 3D block field receding to horizon
    camera.position.set(0, 3.2, 11.8);
    camera.lookAt(0, 0.2, 0);

    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;

    // Soft ambient bounce light (no harsh specular reflection)
    const ambientLight = new THREE.AmbientLight(0xf5edff, 1.4);
    scene.add(ambientLight);

    // Warm key light from top-left
    const keyLight = new THREE.DirectionalLight(0xffeedd, 1.2);
    keyLight.position.set(-8, 12, 8);
    scene.add(keyLight);

    // Soft lavender fill light
    const fillLight = new THREE.DirectionalLight(0xd4c2fb, 0.8);
    fillLight.position.set(8, 6, 4);
    scene.add(fillLight);

    // -------------------------------------------------------------------
    // Grid of Separate Raised 3D Tiles (Matching Reference):
    // - Many small square blocks with small gaps
    // - Light purple tops (#B7A2F0), darker purple sides/fronts (#8E76E0)
    // - Stepped random heights (0 to 14px equivalent)
    // - Matte finish with no metalness (removes bright white vertical center line)
    // - Perspective receding to the horizon
    // -------------------------------------------------------------------
    const floorGroup = new THREE.Group();
    scene.add(floorGroup);

    const baseTileW = 0.76;
    const baseTileH = 0.42;
    const cubeGeom = new THREE.BoxGeometry(baseTileW, baseTileH, baseTileW);

    // Materials: matte light purple top, darker purple front/sides
    const topMaterial = new THREE.MeshStandardMaterial({
      color: 0xb7a2f0,
      roughness: 0.58,
      metalness: 0.0,
    });

    const sideMaterial = new THREE.MeshStandardMaterial({
      color: 0x8e76e0,
      roughness: 0.62,
      metalness: 0.0,
    });

    const bottomMaterial = new THREE.MeshBasicMaterial({
      color: 0x7a62ce,
    });

    const materials = [
      sideMaterial,   // +X (right)
      sideMaterial,   // -X (left)
      topMaterial,    // +Y (top face)
      bottomMaterial, // -Y (bottom)
      sideMaterial,   // +Z (front)
      sideMaterial,   // -Z (back)
    ];

    const rows = 26;
    const cols = 40;
    const spacingX = 0.86;
    const spacingZ = 0.86;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const x = (c - cols / 2 + 0.5) * spacingX;
        const z = (r - rows / 2 + 0.5) * spacingZ;

        // Pseudo-random discrete step height variations
        const hash = Math.sin(c * 12.9898 + r * 78.233) * 43758.5453;
        const rand = hash - Math.floor(hash);

        // Discrete stepped voxel heights (0, 1, 2, 3, 4 steps)
        const stepLevel = Math.floor(rand * 5);
        const heightOffset = stepLevel * 0.065;
        const baseHeight = 0.32 + heightOffset;

        // Taper slightly as it approaches the horizon
        const distFromHorizon = Math.max(0.2, 1 - r / (rows * 0.96));
        const finalHeight = baseHeight * distFromHorizon;
        const scaleY = finalHeight / baseTileH;

        const cube = new THREE.Mesh(cubeGeom, materials);
        cube.scale.set(1, scaleY, 1);
        cube.position.set(x, scaleY * (baseTileH / 2) - 0.72, z);
        floorGroup.add(cube);
      }
    }

    // Parallax mouse interaction
    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      targetMouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      targetMouseY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
    };

    window.addEventListener('mousemove', handleMouseMove);

    const handleResize = () => {
      if (!container) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    let animationId: number;
    const animate = () => {
      animationId = requestAnimationFrame(animate);

      // Subtle, smooth camera parallax
      mouseX += (targetMouseX - mouseX) * 0.03;
      mouseY += (targetMouseY - mouseY) * 0.03;

      camera.position.x = mouseX * 0.35;
      camera.position.y = 3.2 + mouseY * 0.15;
      camera.lookAt(mouseX * 0.12, 0.2, 0);

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
      renderer.dispose();
      cubeGeom.dispose();
      topMaterial.dispose();
      sideMaterial.dispose();
      bottomMaterial.dispose();
      scene.clear();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-x-0 bottom-0 h-[44%] w-full pointer-events-none select-none overflow-hidden"
      style={{
        maskImage:
          'linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0.95) 35%, rgba(0,0,0,0.3) 70%, rgba(0,0,0,0) 95%)',
        WebkitMaskImage:
          'linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0.95) 35%, rgba(0,0,0,0.3) 70%, rgba(0,0,0,0) 95%)',
      }}
    >
      <canvas ref={canvasRef} className="w-full h-full block pointer-events-auto" />
    </div>
  );
};
