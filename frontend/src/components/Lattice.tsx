'use client';

import { useRef, useMemo, useEffect, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Sphere, Line, Html } from '@react-three/drei';
import * as THREE from 'three';
import { InfrastructureNode, AgentState } from '@/types';

// ============================================
// Shader for Pulsing Glow Effect
// ============================================
const pulseVertexShader = `
  varying vec3 vNormal;
  varying vec3 vPosition;
  
  void main() {
    vNormal = normalize(normalMatrix * normal);
    vPosition = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const pulseFragmentShader = `
  uniform vec3 color;
  uniform float time;
  uniform float intensity;
  varying vec3 vNormal;
  varying vec3 vPosition;
  
  void main() {
    float pulse = sin(time * 2.0) * 0.5 + 0.5;
    float fresnel = pow(1.0 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
    vec3 glow = color * (0.5 + pulse * intensity * 0.5);
    float alpha = fresnel * (0.6 + pulse * 0.4);
    gl_FragColor = vec4(glow, alpha);
  }
`;

// ============================================
// Lattice Node Component
// ============================================
interface LatticeNodeProps {
    node: InfrastructureNode;
    isActive: boolean;
    agentState: AgentState;
}

function LatticeNode({ node, isActive, agentState }: LatticeNodeProps) {
    const meshRef = useRef<THREE.Mesh>(null);
    const glowRef = useRef<THREE.Mesh>(null);
    const [hovered, setHovered] = useState(false);

    // Determine color based on node status and agent state
    const color = useMemo(() => {
        if (node.status === 'error' || agentState === 'STROBE_RED') {
            return new THREE.Color('#FF0000');
        }
        if (node.status === 'processing' || agentState === 'RAPID_PULSE') {
            return new THREE.Color('#FFFFFF');
        }
        if (node.status === 'warning') {
            return new THREE.Color('#FFAA00');
        }
        if (agentState === 'SUCCESS') {
            return new THREE.Color('#00FF00');
        }
        return new THREE.Color('#0070F3');
    }, [node.status, agentState]);

    // Shader uniforms
    const uniforms = useMemo(() => ({
        color: { value: color },
        time: { value: 0 },
        intensity: { value: isActive ? 1.0 : 0.5 },
    }), [color, isActive]);

    // Animation loop
    useFrame((state) => {
        if (meshRef.current) {
            // Breathing animation
            const scale = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.05;
            meshRef.current.scale.setScalar(isActive ? scale : 1);
        }

        if (glowRef.current && glowRef.current.material) {
            uniforms.time.value = state.clock.elapsedTime;
        }
    });

    // Node size based on type
    const size = useMemo(() => {
        switch (node.type) {
            case 'service': return 0.8;
            case 'database': return 0.7;
            case 'api': return 0.6;
            case 'file': return 0.4;
            default: return 0.5;
        }
    }, [node.type]);

    return (
        <group position={node.position}>
            {/* Core node */}
            <Sphere
                ref={meshRef}
                args={[size, 32, 32]}
                onPointerOver={() => setHovered(true)}
                onPointerOut={() => setHovered(false)}
            >
                <meshStandardMaterial
                    color={color}
                    emissive={color}
                    emissiveIntensity={isActive ? 0.8 : 0.3}
                    roughness={0.2}
                    metalness={0.8}
                />
            </Sphere>

            {/* Glow shell */}
            <Sphere ref={glowRef} args={[size * 1.3, 32, 32]}>
                <shaderMaterial
                    vertexShader={pulseVertexShader}
                    fragmentShader={pulseFragmentShader}
                    uniforms={uniforms}
                    transparent
                    side={THREE.BackSide}
                    depthWrite={false}
                />
            </Sphere>

            {/* Label on hover */}
            {hovered && (
                <Html distanceFactor={10}>
                    <div className="card px-3 py-2 text-xs whitespace-nowrap">
                        <div className="text-white font-medium">{node.name}</div>
                        <div className="text-muted text-[10px]">{node.type}</div>
                    </div>
                </Html>
            )}
        </group>
    );
}

// ============================================
// Connection Lines Between Nodes
// ============================================
interface ConnectionLineProps {
    start: [number, number, number];
    end: [number, number, number];
    active: boolean;
    agentState: AgentState;
}

function ConnectionLine({ start, end, active, agentState }: ConnectionLineProps) {
    const color = useMemo(() => {
        if (agentState === 'STROBE_RED') return '#FF0000';
        if (agentState === 'SUCCESS') return '#00FF00';
        if (active) return '#0070F3';
        return '#1A1A1A';
    }, [agentState, active]);

    return (
        <Line
            points={[start, end]}
            color={color}
            lineWidth={active ? 2 : 1}
            transparent
            opacity={active ? 0.8 : 0.3}
        />
    );
}

// ============================================
// Camera Controls with Auto-Rotation
// ============================================
function CameraController({ autoRotate }: { autoRotate: boolean }) {
    const { camera } = useThree();

    useEffect(() => {
        camera.position.set(0, 5, 20);
        camera.lookAt(0, 0, 0);
    }, [camera]);

    return (
        <OrbitControls
            enableZoom={true}
            enablePan={true}
            autoRotate={autoRotate}
            autoRotateSpeed={0.5}
            minDistance={10}
            maxDistance={50}
            dampingFactor={0.05}
            enableDamping
        />
    );
}

// ============================================
// Main Lattice Component
// ============================================
interface LatticeProps {
    nodes: InfrastructureNode[];
    activeNodeId?: string;
    agentState: AgentState;
}

export default function Lattice({ nodes, activeNodeId, agentState }: LatticeProps) {
    const [autoRotate, setAutoRotate] = useState(true);

    // Generate connection pairs from node connections
    const connections = useMemo(() => {
        const pairs: { start: [number, number, number]; end: [number, number, number]; active: boolean }[] = [];

        nodes.forEach(node => {
            node.connections.forEach(connId => {
                const targetNode = nodes.find(n => n.id === connId);
                if (targetNode) {
                    pairs.push({
                        start: node.position,
                        end: targetNode.position,
                        active: node.id === activeNodeId || connId === activeNodeId,
                    });
                }
            });
        });

        return pairs;
    }, [nodes, activeNodeId]);

    // Pause auto-rotate when agent is active
    useEffect(() => {
        if (agentState === 'RAPID_PULSE' || agentState === 'STROBE_RED') {
            setAutoRotate(false);
        } else if (agentState === 'IDLE' || agentState === 'BREATHE') {
            const timer = setTimeout(() => setAutoRotate(true), 3000);
            return () => clearTimeout(timer);
        }
    }, [agentState]);

    return (
        <div className="canvas-container relative">
            {/* State indicator overlay */}
            <div className="absolute top-4 left-4 z-10 flex items-center gap-2">
                <div className={`status-dot ${agentState === 'IDLE' ? 'idle' :
                    agentState === 'STROBE_RED' ? 'error' :
                        agentState === 'SUCCESS' ? 'success' : 'active'
                    }`} />
                <span className="text-xs font-mono text-muted">{agentState}</span>
            </div>

            <Canvas
                camera={{ position: [0, 5, 20], fov: 60 }}
                gl={{ antialias: true, alpha: true }}
                style={{ background: '#000000' }}
            >
                {/* Ambient lighting */}
                <ambientLight intensity={0.2} />

                {/* Dynamic point light based on state */}
                <pointLight
                    position={[10, 10, 10]}
                    color={
                        agentState === 'STROBE_RED' ? '#FF0000' :
                            agentState === 'SUCCESS' ? '#00FF00' : '#0070F3'
                    }
                    intensity={1.5}
                />
                <pointLight position={[-10, -10, -10]} color="#0070F3" intensity={0.5} />

                {/* Grid helper for reference */}
                <gridHelper args={[30, 30, '#1A1A1A', '#0A0A0A']} />

                {/* Render connection lines */}
                {connections.map((conn, i) => (
                    <ConnectionLine
                        key={`conn-${i}`}
                        start={conn.start}
                        end={conn.end}
                        active={conn.active}
                        agentState={agentState}
                    />
                ))}

                {/* Render nodes */}
                {nodes.map(node => (
                    <LatticeNode
                        key={node.id}
                        node={node}
                        isActive={node.id === activeNodeId}
                        agentState={agentState}
                    />
                ))}

                {/* Camera controls */}
                <CameraController autoRotate={autoRotate} />
            </Canvas>
        </div>
    );
}
