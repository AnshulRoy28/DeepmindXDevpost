// Type definitions for NEURO-SENTINEL

export type AgentState = 'IDLE' | 'BREATHE' | 'RAPID_PULSE' | 'STROBE_RED' | 'SUCCESS';

export interface Thought {
    id: string;
    timestamp: Date;
    type: 'reasoning' | 'action' | 'error' | 'system';
    content: string;
    signature?: string; // Thought Signature for reasoning persistence
}

export interface InfrastructureNode {
    id: string;
    name: string;
    type: 'file' | 'service' | 'database' | 'api' | 'dependency';
    path?: string;
    status: 'healthy' | 'warning' | 'error' | 'processing';
    position: [number, number, number];
    connections: string[]; // IDs of connected nodes
    metadata?: Record<string, unknown>;
}

export interface SystemState {
    agentState: AgentState;
    nodes: InfrastructureNode[];
    activeNodeId?: string;
    thoughts: Thought[];
    tokenUsage: {
        current: number;
        max: number;
    };
    lastAction?: {
        type: string;
        target: string;
        timestamp: Date;
    };
}

export interface AgentStateUpdate {
    state: AgentState;
    thought?: string;
    signature?: string;
    affectedNodes?: string[];
}

export interface SocketEvents {
    // Client -> Server
    'request_state': () => void;
    'trigger_analysis': (data: { target: string }) => void;
    'simulate_error': (data: { nodeId: string; error: string }) => void;

    // Server -> Client
    'agent_state': (data: AgentStateUpdate) => void;
    'thought_update': (data: Thought) => void;
    'node_update': (data: InfrastructureNode) => void;
    'system_state': (data: SystemState) => void;
}
