'use client';

import { motion } from 'framer-motion';
import { AgentState } from '@/types';

// ============================================
// Status Card Component
// ============================================
interface StatusCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    icon?: string;
    state?: AgentState;
    variant?: 'default' | 'large' | 'compact';
}

export function StatusCard({
    title,
    value,
    subtitle,
    icon,
    state = 'IDLE',
    variant = 'default',
}: StatusCardProps) {
    const stateColors = {
        IDLE: '#888888',
        BREATHE: '#0070F3',
        RAPID_PULSE: '#FFFFFF',
        STROBE_RED: '#FF0000',
        SUCCESS: '#00FF00',
    };

    return (
        <div className={`card ${variant === 'compact' ? 'p-3' : 'p-4'}`}>
            <div className="flex items-start justify-between mb-2">
                <span className="text-muted text-xs uppercase tracking-wide">
                    {title}
                </span>
                {icon && (
                    <span className="text-muted text-sm">{icon}</span>
                )}
            </div>

            <div className={`font-mono font-medium ${variant === 'large' ? 'text-2xl' : 'text-lg'
                }`} style={{ color: stateColors[state] }}>
                {value}
            </div>

            {subtitle && (
                <div className="text-muted text-xs mt-1">
                    {subtitle}
                </div>
            )}
        </div>
    );
}

// ============================================
// Token Usage Card
// ============================================
interface TokenUsageCardProps {
    current: number;
    max: number;
}

export function TokenUsageCard({ current, max }: TokenUsageCardProps) {
    const percentage = Math.min((current / max) * 100, 100);

    const formatNumber = (n: number) => {
        if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
        if (n >= 1000) return `${(n / 1000).toFixed(0)}K`;
        return n.toString();
    };

    return (
        <div className="card p-4">
            <div className="flex items-center justify-between mb-3">
                <span className="text-muted text-xs uppercase tracking-wide">
                    Context Usage
                </span>
                <span className="text-xs font-mono text-muted">
                    {formatNumber(current)} / {formatNumber(max)}
                </span>
            </div>

            {/* Progress bar */}
            <div className="h-1.5 bg-[#1A1A1A] rounded-full overflow-hidden">
                <motion.div
                    className="h-full rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                    style={{
                        backgroundColor:
                            percentage > 90 ? '#FF0000' :
                                percentage > 70 ? '#FFAA00' : '#0070F3'
                    }}
                />
            </div>

            <div className="mt-2 text-xs text-muted">
                {percentage.toFixed(1)}% utilized
            </div>
        </div>
    );
}

// ============================================
// Agent State Card
// ============================================
interface AgentStateCardProps {
    state: AgentState;
    lastActionType?: string;
    lastActionTarget?: string;
    lastActionTime?: Date;
}

export function AgentStateCard({
    state,
    lastActionType,
    lastActionTarget,
    lastActionTime,
}: AgentStateCardProps) {
    const stateInfo = {
        IDLE: { label: 'System Idle', color: '#888888', animation: '' },
        BREATHE: { label: 'Monitoring', color: '#0070F3', animation: 'animate-breathe' },
        RAPID_PULSE: { label: 'Reasoning', color: '#FFFFFF', animation: 'animate-rapid-pulse' },
        STROBE_RED: { label: 'Error Detected', color: '#FF0000', animation: 'animate-strobe-red' },
        SUCCESS: { label: 'Surgery Complete', color: '#00FF00', animation: '' },
    };

    const info = stateInfo[state];

    const formatTime = (date?: Date) => {
        if (!date) return '--:--:--';
        return new Date(date).toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        });
    };

    return (
        <div className="card p-4">
            {/* State indicator */}
            <div className="flex items-center gap-3 mb-4">
                <div
                    className={`w-4 h-4 rounded-full ${info.animation}`}
                    style={{ backgroundColor: info.color }}
                />
                <div>
                    <div className="text-white font-medium">{info.label}</div>
                    <div className="text-muted text-xs font-mono">{state}</div>
                </div>
            </div>

            {/* Last action */}
            <div className="border-t border-[#1A1A1A] pt-3 mt-3">
                <div className="text-muted text-xs uppercase tracking-wide mb-2">
                    Last Action
                </div>
                <div className="space-y-1">
                    <div className="flex items-center justify-between">
                        <span className="text-muted text-xs">Type:</span>
                        <span className="text-white text-xs font-mono">
                            {lastActionType || 'None'}
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-muted text-xs">Target:</span>
                        <span className="text-white text-xs font-mono truncate max-w-[120px]">
                            {lastActionTarget || '--'}
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-muted text-xs">Time:</span>
                        <span className="text-white text-xs font-mono">
                            {formatTime(lastActionTime)}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ============================================
// Connection Status Card
// ============================================
interface ConnectionStatusCardProps {
    isConnected: boolean;
    serverUrl: string;
    latency?: number;
}

export function ConnectionStatusCard({
    isConnected,
    serverUrl,
    latency,
}: ConnectionStatusCardProps) {
    return (
        <div className="card p-4">
            <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500 animate-pulse'
                    }`} />
                <div className="flex-1 min-w-0">
                    <div className="text-white text-sm font-medium">
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </div>
                    <div className="text-muted text-xs font-mono truncate">
                        {serverUrl}
                    </div>
                </div>
                {latency !== undefined && isConnected && (
                    <div className="text-muted text-xs font-mono">
                        {latency}ms
                    </div>
                )}
            </div>
        </div>
    );
}

export default StatusCard;
