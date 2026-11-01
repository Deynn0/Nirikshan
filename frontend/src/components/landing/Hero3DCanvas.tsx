import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export const Hero3DCanvas: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    // Check WebGL availability safely
    let renderer: THREE.WebGLRenderer | null = null;
    try {
      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
      if (!gl) {
        return;
      }
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

    // Camera setup
    const camera = new THREE.PerspectiveCamera(38, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 0.8, 11);

    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;

    // Lights
    const ambientLight = new THREE.AmbientLight(0xfff3ea, 1.4);
    scene.add(ambientLight);

    const dirLightTopLeft = new THREE.DirectionalLight(0xffffff, 2.2);
    dirLightTopLeft.position.set(-6, 9, 7);
    scene.add(dirLightTopLeft);

    const fillLightRight = new THREE.DirectionalLight(0xc4b5fd, 1.6);
    fillLightRight.position.set(6, 4, 3);
    scene.add(fillLightRight);

    const rimLight = new THREE.DirectionalLight(0xffa5c4, 1.0);
    rimLight.position.set(0, -3, -4);
    scene.add(rimLight);

    // Root groups
    const mainGroup = new THREE.Group();
    scene.add(mainGroup);

    const handsGroup = new THREE.Group();
    mainGroup.add(handsGroup);

    const floorGroup = new THREE.Group();
    mainGroup.add(floorGroup);

    // ----------------------------------------------------
    // 1. Perspective Floor of Purple/Lavender Cubes (Pixel-Block Landscape)
    // ----------------------------------------------------
    const cubeGeom = new THREE.BoxGeometry(0.55, 1, 0.55);

    // Color ramp from soft lavender to deep violet
    const purpleColors = [
      new THREE.Color('#E9D5FF'), // lavender-200
      new THREE.Color('#D8B4FE'), // lavender-300
      new THREE.Color('#C084FC'), // purple-400
      new THREE.Color('#A855F7'), // purple-500
      new THREE.Color('#9333EA'), // purple-600
      new THREE.Color('#7E22CE'), // purple-700
      new THREE.Color('#6B21A8'), // purple-800
      new THREE.Color('#581C87'), // purple-900
    ];

    const gridRows = 16;
    const gridCols = 22;
    const spacing = 0.62;

    for (let r = 0; r < gridRows; r++) {
      for (let c = 0; c < gridCols; c++) {
        // Vary heights based on noise/sine and distance
        const xPos = (c - gridCols / 2) * spacing;
        const zPos = (r - gridRows / 2) * spacing - 1.5;

        // Wave heights
        const distFromCenter = Math.sqrt(xPos * xPos + zPos * zPos);
        const heightFactor = Math.sin(xPos * 0.8) * Math.cos(zPos * 0.7);
        const randomVar = ((c * 17 + r * 31) % 10) / 10;
        const baseHeight = 0.35 + Math.abs(heightFactor) * 1.1 + randomVar * 0.45;

        // Taper down near horizon (high r) and near front center
        const horizonFade = Math.max(0.1, 1 - r / (gridRows * 0.95));
        const finalHeight = baseHeight * horizonFade;

        // Material color by height and row
        const colorIdx = Math.floor(
          Math.min(purpleColors.length - 1, (randomVar * 0.4 + (1 - r / gridRows) * 0.6) * purpleColors.length)
        );
        const color = purpleColors[colorIdx];

        const cubeMat = new THREE.MeshStandardMaterial({
          color,
          roughness: 0.35,
          metalness: 0.08,
        });

        const cube = new THREE.Mesh(cubeGeom, cubeMat);
        cube.scale.set(1, finalHeight, 1);
        cube.position.set(xPos, -3.2 + finalHeight / 2, zPos);
        floorGroup.add(cube);
      }
    }

    // Tilt floor slightly backward
    floorGroup.position.set(0, -0.6, 0);
    floorGroup.rotation.x = 0.08;

    // ----------------------------------------------------
    // 2. Toy-Like 3D Hands Making "OK" Gesture with Eye
    // ----------------------------------------------------
    // Helper to create a stylized OK-gesture hand
    const createHand = (colorHex: string, isLeft: boolean) => {
      const hand = new THREE.Group();

      const handMaterial = new THREE.MeshPhysicalMaterial({
        color: new THREE.Color(colorHex),
        roughness: 0.22,
        metalness: 0.05,
        clearcoat: 0.75,
        clearcoatRoughness: 0.15,
      });

      // (A) Wrist / Forearm rising from floor
      const armGeom = new THREE.CylinderGeometry(0.72, 0.85, 3.2, 32);
      const armMesh = new THREE.Mesh(armGeom, handMaterial);
      armMesh.position.set(0, -1.8, 0);
      hand.add(armMesh);

      // (B) Palm
      const palmGeom = new THREE.SphereGeometry(0.95, 32, 24);
      const palmMesh = new THREE.Mesh(palmGeom, handMaterial);
      palmMesh.scale.set(1.1, 1.25, 0.75);
      palmMesh.position.set(0, 0, 0);
      hand.add(palmMesh);

      // (C) "OK" circle: Thumb & Index finger meeting in a ring
      // We use a Torus for the clean curved circle
      const ringGeom = new THREE.TorusGeometry(0.68, 0.22, 24, 48);
      const ringMesh = new THREE.Mesh(ringGeom, handMaterial);
      ringMesh.position.set(isLeft ? 0.75 : -0.75, 0.35, 0.45);
      ringMesh.rotation.y = isLeft ? -0.3 : 0.3;
      ringMesh.rotation.z = isLeft ? 0.25 : -0.25;
      hand.add(ringMesh);

      // (D) Single Cartoon Eye inside the circle formed by thumb & index finger
      const eyeGroup = new THREE.Group();
      eyeGroup.position.copy(ringMesh.position);

      // Sclera (white sphere)
      const scleraGeom = new THREE.SphereGeometry(0.48, 32, 24);
      const scleraMat = new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.08,
        metalness: 0.02,
      });
      const sclera = new THREE.Mesh(scleraGeom, scleraMat);
      eyeGroup.add(sclera);

      // Pupil (black sphere pupil)
      const pupilGeom = new THREE.SphereGeometry(0.22, 24, 20);
      const pupilMat = new THREE.MeshBasicMaterial({ color: 0x0a0a0f });
      const pupil = new THREE.Mesh(pupilGeom, pupilMat);
      pupil.scale.set(1, 1, 0.4);
      pupil.position.set(0, 0, 0.42);
      eyeGroup.add(pupil);

      // Cute white catchlight glint
      const glintGeom = new THREE.SphereGeometry(0.07, 16, 16);
      const glintMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      const glint = new THREE.Mesh(glintGeom, glintMat);
      glint.position.set(0.07, 0.08, 0.51);
      eyeGroup.add(glint);

      hand.add(eyeGroup);

      // (E) The 3 upright extended fingers (Middle, Ring, Pinky)
      const createFinger = (
        length: number,
        radius: number,
        xPos: number,
        yPos: number,
        zRot: number,
        xRot: number
      ) => {
        const finger = new THREE.Group();
        const fGeom = new THREE.CapsuleGeometry(radius, length, 16, 24);
        const fMesh = new THREE.Mesh(fGeom, handMaterial);
        fMesh.position.set(0, length / 2, 0);
        finger.add(fMesh);
        finger.position.set(xPos, yPos, 0);
        finger.rotation.z = zRot;
        finger.rotation.x = xRot;
        return finger;
      };

      const sign = isLeft ? 1 : -1;

      // Middle finger (tallest)
      const middleFinger = createFinger(1.5, 0.22, -0.32 * sign, 0.95, -0.08 * sign, -0.15);
      hand.add(middleFinger);

      // Ring finger
      const ringFinger = createFinger(1.35, 0.2, -0.72 * sign, 0.8, -0.22 * sign, -0.1);
      hand.add(ringFinger);

      // Pinky finger (smallest)
      const pinkyFinger = createFinger(1.15, 0.18, -1.08 * sign, 0.6, -0.38 * sign, -0.05);
      hand.add(pinkyFinger);

      return { hand, eyeGroup, pupil };
    };

    // Left hand: Pink/salmon (#FF758F / #FF8096)
    const leftHandObj = createHand('#FF758F', true);
    leftHandObj.hand.position.set(-1.65, -0.4, -0.2);
    leftHandObj.hand.rotation.set(0.08, 0.28, -0.14);
    leftHandObj.hand.scale.set(1.12, 1.12, 1.12);
    handsGroup.add(leftHandObj.hand);

    // Right hand: Deep violet/purple (#6D28D9 / #7C3AED)
    const rightHandObj = createHand('#6D28D9', false);
    rightHandObj.hand.position.set(1.35, -0.65, 0.5);
    rightHandObj.hand.rotation.set(-0.05, -0.32, 0.18);
    rightHandObj.hand.scale.set(1.22, 1.22, 1.22);
    handsGroup.add(rightHandObj.hand);

    // Subtle contact shadows under hands
    const shadowMat = new THREE.MeshBasicMaterial({
      color: 0x4c1d95,
      transparent: true,
      opacity: 0.18,
    });
    const shadowGeom = new THREE.CircleGeometry(1.6, 32);

    const shadowLeft = new THREE.Mesh(shadowGeom, shadowMat);
    shadowLeft.rotation.x = -Math.PI / 2;
    shadowLeft.position.set(-1.6, -2.45, -0.2);
    handsGroup.add(shadowLeft);

    const shadowRight = new THREE.Mesh(shadowGeom, shadowMat);
    shadowRight.rotation.x = -Math.PI / 2;
    shadowRight.position.set(1.35, -2.45, 0.5);
    handsGroup.add(shadowRight);

    // ----------------------------------------------------
    // Mouse Interaction for Parallax and Eye Tracking
    // ----------------------------------------------------
    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      targetMouseX = Math.max(-1, Math.min(1, x));
      targetMouseY = Math.max(-1, Math.min(1, y));
    };

    window.addEventListener('mousemove', handleMouseMove);

    // Responsive Resize Handler
    const handleResize = () => {
      if (!container) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      camera.aspect = width / height;

      // Adjust camera distance for mobile responsiveness
      if (width < 640) {
        camera.position.z = 15;
        camera.position.y = 0.4;
      } else if (width < 1024) {
        camera.position.z = 13;
        camera.position.y = 0.6;
      } else {
        camera.position.z = 11;
        camera.position.y = 0.8;
      }

      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    // ----------------------------------------------------
    // Animation Loop
    // ----------------------------------------------------
    let clock = new THREE.Clock();
    let animationFrameId: number;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Smooth mouse lerp
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      // Slow floating / bobbing animation with phase difference
      const leftBob = Math.sin(elapsedTime * 1.3) * 0.12;
      const rightBob = Math.sin(elapsedTime * 1.3 + 1.2) * 0.14;

      leftHandObj.hand.position.y = -0.4 + leftBob;
      rightHandObj.hand.position.y = -0.65 + rightBob;

      // Gentle floating tilt
      leftHandObj.hand.rotation.z = -0.14 + Math.cos(elapsedTime * 0.9) * 0.04;
      rightHandObj.hand.rotation.z = 0.18 + Math.cos(elapsedTime * 0.9 + 1.4) * 0.04;

      // Parallax rotation of the entire hands group
      handsGroup.rotation.y = mouseX * 0.22;
      handsGroup.rotation.x = -mouseY * 0.15;

      // Subtle parallax tilt on floor
      floorGroup.rotation.y = mouseX * 0.08;
      floorGroup.rotation.x = 0.08 - mouseY * 0.05;

      // Eyes follow mouse slightly
      const eyeLookX = mouseX * 0.12;
      const eyeLookY = mouseY * 0.12;
      leftHandObj.pupil.position.x = eyeLookX;
      leftHandObj.pupil.position.y = eyeLookY;
      rightHandObj.pupil.position.x = eyeLookX;
      rightHandObj.pupil.position.y = eyeLookY;

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);

      // Clean disposal
      renderer.dispose();
      cubeGeom.dispose();
      purpleColors.forEach(() => {});
      scene.clear();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full min-h-[460px] sm:min-h-[540px] lg:min-h-[620px] flex items-center justify-center pointer-events-none select-none"
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full absolute inset-0 block pointer-events-auto"
      />
    </div>
  );
};
