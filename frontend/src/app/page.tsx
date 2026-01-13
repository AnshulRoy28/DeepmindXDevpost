'use client';

import { useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import ThoughtStream from '@/components/ThoughtStream';
import {
  StatusCard,
  TokenUsageCard,
  AgentStateCard,
  ConnectionStatusCard
} from '@/components/StatusCard';
import socketManager from '@/lib/socket';
import { AgentState, Thought, InfrastructureNode, SystemState } from '@/types';

// Dynamic import for Three.js component (no SSR)
const Lattice = dynamic(() => import('@/components/Lattice'), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full flex items-center justify-center bg-black">
      <div className="text-muted font-mono text-sm animate-pulse">
        Initializing Logic Lattice...
      </div>
    </div>
  ),
});

// ============================================
// Demo Data Generator (for testing without backend)
// ============================================
function generateDemoNodes(): InfrastructureNode[] {
  return [
    { id: 'core', name: 'agent_core.py', type: 'service', status: 'healthy', position: [0, 0, 0], connections: ['ingestor', 'tools'] },
    { id: 'ingestor', name: 'ingestor.py', type: 'service', status: 'healthy', position: [-5, 2, 3], connections: ['core'] },
    { id: 'tools', name: 'tools.py', type: 'api', status: 'healthy', position: [5, 2, -2], connections: ['core', 'git'] },
    { id: 'git', name: 'git_handler', type: 'service', status: 'healthy', position: [8, -1, 0], connections: ['tools'] },
    { id: 'socket', name: 'socket_manager.py', type: 'api', status: 'healthy', position: [-3, -3, 5], connections: ['core'] },
    { id: 'db', name: 'state_store', type: 'database', status: 'healthy', position: [3, -4, -4], connections: ['core'] },
    { id: 'frontend', name: 'dashboard', type: 'service', status: 'healthy', position: [-6, 0, -5], connections: ['socket'] },
    { id: 'pi', name: 'raspberry_pi', type: 'service', status: 'healthy', position: [-8, -2, 2], connections: ['socket'] },
  ];
}

function generateDemoThought(type: Thought['type']): Thought {
  const contents = {
    reasoning: [
      'Analyzing stack trace in 1M token context...',
      'Cross-referencing error signature with historical patterns...',
      'Evaluating potential root causes in dependency graph...',
      'Synthesizing patch strategy from codebase context...',
      'Validating proposed fix against type constraints...',
    ],
    action: [
      'Executing git diff to identify recent changes...',
      'Reading logs from service monitor...',
      'Applying patch to core.py line 142...',
      'Running verification tests...',
      'Committing fix with signature: AUTO-FIX-001',
    ],
    error: [
      'TypeError detected in module initialization',
      'Connection timeout to database cluster',
      'Memory allocation exceeded threshold',
    ],
    system: [
      'Heartbeat received from Raspberry Pi display',
      'Context ingestion complete: 847,291 tokens processed',
      'Entering monitoring mode...',
    ],
  };

  const options = contents[type];
  return {
    id: `thought-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date(),
    type,
    content: options[Math.floor(Math.random() * options.length)],
    signature: type === 'reasoning' ? `SIG-${Math.random().toString(36).substr(2, 4).toUpperCase()}` : undefined,
  };
}

// ============================================
// Main Dashboard Page
// ============================================
export default function Dashboard() {
  // State management
  const [isConnected, setIsConnected] = useState(false);
  const [agentState, setAgentState] = useState<AgentState>('IDLE');
  const [nodes, setNodes] = useState<InfrastructureNode[]>(generateDemoNodes());
  const [activeNodeId, setActiveNodeId] = useState<string | undefined>();
  const [thoughts, setThoughts] = useState<Thought[]>([]);
  const [tokenUsage, setTokenUsage] = useState({ current: 0, max: 1000000 });
  const [lastAction, setLastAction] = useState<{
    type: string;
    target: string;
    timestamp: Date;
  } | undefined>();

  // Socket connection
  useEffect(() => {
    const socket = socketManager.connect();

    socket.on('connect', () => setIsConnected(true));
    socket.on('disconnect', () => setIsConnected(false));

    // Subscribe to events
    const unsubState = socketManager.onAgentState((data) => {
      setAgentState(data.state);
      if (data.thought) {
        const newThought: Thought = {
          id: `thought-${Date.now()}`,
          timestamp: new Date(),
          type: data.state === 'STROBE_RED' ? 'error' : 'reasoning',
          content: data.thought,
          signature: data.signature,
        };
        setThoughts(prev => [...prev, newThought]);
      }
      if (data.affectedNodes) {
        setActiveNodeId(data.affectedNodes[0]);
      }
    });

    const unsubThought = socketManager.onThoughtUpdate((thought) => {
      setThoughts(prev => [...prev, thought]);
    });

    const unsubNode = socketManager.onNodeUpdate((node) => {
      setNodes(prev => prev.map(n => n.id === node.id ? node : n));
    });

    const unsubSystem = socketManager.onSystemState((state) => {
      setAgentState(state.agentState);
      // Only update nodes if the server provides them (non-empty)
      if (state.nodes && state.nodes.length > 0) {
        setNodes(state.nodes);
      }
      setActiveNodeId(state.activeNodeId);
      // Only update thoughts if provided
      if (state.thoughts && state.thoughts.length > 0) {
        setThoughts(state.thoughts);
      }
      setTokenUsage(state.tokenUsage);
      if (state.lastAction) {
        setLastAction(state.lastAction);
      }
    });

    // Request initial state
    socketManager.requestState();

    return () => {
      unsubState();
      unsubThought();
      unsubNode();
      unsubSystem();
      socketManager.disconnect();
    };
  }, []);

  // Demo mode simulation (when not connected to backend)
  useEffect(() => {
    if (isConnected) return;

    // Simulate initial thoughts
    const initialThoughts: Thought[] = [
      { id: '1', timestamp: new Date(), type: 'system', content: 'NEURO-SENTINEL initialized. Awaiting backend connection...' },
      { id: '2', timestamp: new Date(Date.now() + 100), type: 'system', content: 'Demo mode active. Connect backend to enable live surgery.' },
    ];
    setThoughts(initialThoughts);
    setTokenUsage({ current: 0, max: 1000000 });

    // Periodic demo updates
    const demoInterval = setInterval(() => {
      // Cycle through states for demo
      setAgentState(prev => {
        const states: AgentState[] = ['IDLE', 'BREATHE', 'BREATHE', 'BREATHE', 'RAPID_PULSE'];
        const idx = states.indexOf(prev);
        return states[(idx + 1) % states.length];
      });

      // Add demo thoughts occasionally
      if (Math.random() > 0.7) {
        const types: Thought['type'][] = ['system', 'reasoning'];
        const type = types[Math.floor(Math.random() * types.length)];
        setThoughts(prev => [...prev.slice(-50), generateDemoThought(type)]);
      }

      // Update token usage
      setTokenUsage(prev => ({
        ...prev,
        current: Math.min(prev.current + Math.floor(Math.random() * 1000), prev.max * 0.3),
      }));
    }, 3000);

    return () => clearInterval(demoInterval);
  }, [isConnected]);

  // Simulate error (demo function)
  const simulateError = useCallback(() => {
    setAgentState('STROBE_RED');
    setActiveNodeId('core');
    setNodes(prev => prev.map(n =>
      n.id === 'core' ? { ...n, status: 'error' as const } : n
    ));
    setThoughts(prev => [...prev, generateDemoThought('error')]);

    // Recovery sequence
    setTimeout(() => {
      setAgentState('RAPID_PULSE');
      setThoughts(prev => [...prev, generateDemoThought('reasoning')]);
    }, 2000);

    setTimeout(() => {
      setThoughts(prev => [...prev, generateDemoThought('reasoning')]);
    }, 3500);

    setTimeout(() => {
      setThoughts(prev => [...prev, generateDemoThought('action')]);
    }, 5000);

    setTimeout(() => {
      setAgentState('SUCCESS');
      setNodes(prev => prev.map(n =>
        n.id === 'core' ? { ...n, status: 'healthy' as const } : n
      ));
      setThoughts(prev => [...prev, {
        id: `fix-${Date.now()}`,
        timestamp: new Date(),
        type: 'action',
        content: '✓ Code surgery complete. System restored to healthy state.',
      }]);
      setLastAction({
        type: 'PATCH',
        target: 'core.py',
        timestamp: new Date(),
      });
    }, 6500);

    setTimeout(() => {
      setAgentState('BREATHE');
      setActiveNodeId(undefined);
    }, 9000);
  }, []);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden">
      {/* Header */}
      <header className="border-b-sentinel px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold tracking-tight">
            <span className="text-white">NEURO</span>
            <span className="text-muted">-</span>
            <span className="text-[#0070F3]">SENTINEL</span>
          </h1>
          <div className="h-4 w-px bg-[#1A1A1A]" />
          <span className="text-muted text-xs font-mono uppercase tracking-wider">
            Autonomous Infrastructure Surgeon
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Demo controls */}
          <button
            onClick={simulateError}
            className="px-3 py-1.5 text-xs font-mono bg-red-900/30 text-red-400 
                       border border-red-900 rounded hover:bg-red-900/50 transition-colors"
          >
            Simulate Error
          </button>

          <div className="h-4 w-px bg-[#1A1A1A]" />

          <ConnectionStatusCard
            isConnected={isConnected}
            serverUrl={process.env.NEXT_PUBLIC_SOCKET_URL || 'localhost:8000'}
          />
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left pane - Logic Lattice (60%) */}
        <div className="w-[60%] h-full border-r-sentinel">
          <Lattice
            nodes={nodes}
            activeNodeId={activeNodeId}
            agentState={agentState}
          />
        </div>

        {/* Right pane - Controls & Thought Stream (40%) */}
        <div className="w-[40%] h-full flex flex-col">
          {/* Status cards */}
          <div className="border-b-sentinel p-4 grid grid-cols-2 gap-3">
            <AgentStateCard
              state={agentState}
              lastActionType={lastAction?.type}
              lastActionTarget={lastAction?.target}
              lastActionTime={lastAction?.timestamp}
            />
            <TokenUsageCard
              current={tokenUsage.current}
              max={tokenUsage.max}
            />
          </div>

          {/* Thought Stream */}
          <div className="flex-1 overflow-hidden">
            <ThoughtStream
              thoughts={thoughts}
              agentState={agentState}
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-[#1A1A1A] px-6 py-2 flex items-center justify-between">
        <div className="text-muted text-xs font-mono">
          Powered by Gemini 3 Pro • 1M Token Context
        </div>
        <div className="text-muted text-xs font-mono">
          {new Date().toLocaleTimeString('en-US', { hour12: false })}
        </div>
      </footer>
    </div>
  );
}
