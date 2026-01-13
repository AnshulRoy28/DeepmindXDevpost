'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Thought, AgentState } from '@/types';

// ============================================
// Thought Line Component
// ============================================
interface ThoughtLineProps {
    thought: Thought;
    isNew: boolean;
}

function ThoughtLine({ thought, isNew }: ThoughtLineProps) {
    const typeColors = {
        reasoning: 'thought-type-reasoning',
        action: 'thought-type-action',
        error: 'thought-type-error',
        system: 'text-muted',
    };

    const typeIcons = {
        reasoning: '◆',
        action: '▶',
        error: '✕',
        system: '○',
    };

    const formatTimestamp = (date: Date) => {
        return new Date(date).toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        });
    };

    return (
        <motion.div
            initial={isNew ? { opacity: 0, x: -20 } : false}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="thought-line"
        >
            <div className="flex items-start gap-3">
                {/* Type indicator */}
                <span className={`${typeColors[thought.type]} text-xs mt-0.5`}>
                    {typeIcons[thought.type]}
                </span>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <span className="thought-timestamp">
                            {formatTimestamp(thought.timestamp)}
                        </span>
                        {thought.signature && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#1A1A1A] text-muted">
                                {thought.signature}
                            </span>
                        )}
                    </div>
                    <p className={`${typeColors[thought.type]} break-words`}>
                        {thought.content}
                    </p>
                </div>
            </div>
        </motion.div>
    );
}

// ============================================
// Typing Indicator Component
// ============================================
function TypingIndicator() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-2 py-3 px-4"
        >
            <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                    <motion.div
                        key={i}
                        className="w-2 h-2 rounded-full bg-[#0070F3]"
                        animate={{
                            scale: [1, 1.2, 1],
                            opacity: [0.5, 1, 0.5],
                        }}
                        transition={{
                            duration: 1,
                            repeat: Infinity,
                            delay: i * 0.2,
                        }}
                    />
                ))}
            </div>
            <span className="text-xs text-muted font-mono">Processing...</span>
        </motion.div>
    );
}

// ============================================
// Main ThoughtStream Component
// ============================================
interface ThoughtStreamProps {
    thoughts: Thought[];
    agentState: AgentState;
    maxVisible?: number;
}

export default function ThoughtStream({
    thoughts,
    agentState,
    maxVisible = 100
}: ThoughtStreamProps) {
    const scrollRef = useRef<HTMLDivElement>(null);
    const [autoScroll, setAutoScroll] = useState(true);
    const [newThoughtIds, setNewThoughtIds] = useState<Set<string>>(new Set());

    // Auto-scroll to bottom when new thoughts arrive
    useEffect(() => {
        if (autoScroll && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [thoughts, autoScroll]);

    // Track new thoughts for animation
    useEffect(() => {
        if (thoughts.length > 0) {
            const latestId = thoughts[thoughts.length - 1].id;
            setNewThoughtIds(prev => new Set([...prev, latestId]));

            // Remove from "new" after animation
            const timer = setTimeout(() => {
                setNewThoughtIds(prev => {
                    const next = new Set(prev);
                    next.delete(latestId);
                    return next;
                });
            }, 500);

            return () => clearTimeout(timer);
        }
    }, [thoughts]);

    // Handle scroll to toggle auto-scroll
    const handleScroll = () => {
        if (scrollRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
            const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
            setAutoScroll(isAtBottom);
        }
    };

    // Get visible thoughts
    const visibleThoughts = thoughts.slice(-maxVisible);

    // Is agent thinking?
    const isThinking = agentState === 'RAPID_PULSE' || agentState === 'BREATHE';

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="border-b-sentinel px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-white font-medium text-sm">Thought Stream</span>
                    <span className="text-muted text-xs">
                        ({thoughts.length} entries)
                    </span>
                </div>

                {/* Auto-scroll indicator */}
                <button
                    onClick={() => {
                        setAutoScroll(true);
                        if (scrollRef.current) {
                            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
                        }
                    }}
                    className={`text-xs px-2 py-1 rounded transition-colors ${autoScroll
                            ? 'text-muted bg-transparent'
                            : 'text-white bg-[#0070F3]'
                        }`}
                >
                    {autoScroll ? '⬇ Auto' : '⬇ Jump to latest'}
                </button>
            </div>

            {/* Thought list */}
            <div
                ref={scrollRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto px-4 py-2"
                style={{ scrollBehavior: 'smooth' }}
            >
                {visibleThoughts.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-muted text-sm font-mono">
                        <span>Awaiting agent thoughts...</span>
                    </div>
                ) : (
                    <AnimatePresence mode="popLayout">
                        {visibleThoughts.map((thought) => (
                            <ThoughtLine
                                key={thought.id}
                                thought={thought}
                                isNew={newThoughtIds.has(thought.id)}
                            />
                        ))}
                    </AnimatePresence>
                )}

                {/* Typing indicator when agent is thinking */}
                <AnimatePresence>
                    {isThinking && <TypingIndicator />}
                </AnimatePresence>
            </div>

            {/* Footer - State indicator bar */}
            <div className={`px-4 py-2 border-t border-[#1A1A1A] transition-colors ${agentState === 'STROBE_RED' ? 'bg-red-900/20' :
                    agentState === 'SUCCESS' ? 'bg-green-900/20' :
                        agentState === 'RAPID_PULSE' ? 'bg-blue-900/20' : 'bg-transparent'
                }`}>
                <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${agentState === 'IDLE' ? 'bg-[#888888]' :
                            agentState === 'STROBE_RED' ? 'bg-red-500 animate-pulse' :
                                agentState === 'SUCCESS' ? 'bg-green-500' :
                                    'bg-[#0070F3] animate-pulse'
                        }`} />
                    <span className="text-[11px] font-mono text-muted uppercase">
                        {agentState === 'IDLE' ? 'System Idle' :
                            agentState === 'BREATHE' ? 'Monitoring' :
                                agentState === 'RAPID_PULSE' ? 'Reasoning' :
                                    agentState === 'STROBE_RED' ? 'Error Detected' :
                                        'Surgery Complete'}
                    </span>
                </div>
            </div>
        </div>
    );
}
