import React, { useState } from 'react';
import { mockLinkedNodes, mockLinkedEdges, LinkedNode } from '../../data/mockScrutinyData';
import { Network, ZoomIn, ZoomOut, AlertTriangle, Building2, User, Landmark } from 'lucide-react';
import { PillBadge } from '../common/PillBadge';

export const LinkedApplicationsGraph: React.FC = () => {
  const [selectedNode, setSelectedNode] = useState<LinkedNode | null>(mockLinkedNodes[0]);

  return (
    <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-4 shadow-soft">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-stone-200 dark:border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-purple-600" />
          <h4 className="font-bold text-xs text-stone-900 dark:text-slate-100">
            Linked Applications Graph
          </h4>
        </div>
        <PillBadge variant="critical" size="sm">
          3 Collusions Detected
        </PillBadge>
      </div>

      {/* Interactive SVG Network Canvas */}
      <div className="relative w-full h-64 bg-stone-50 dark:bg-slate-950/60 rounded-xl border border-stone-200/80 dark:border-slate-800 overflow-hidden select-none">
        <svg className="w-full h-full" viewBox="0 0 400 400">
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="4"
              markerHeight="4"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#CBD5E1" />
            </marker>
            <marker
              id="arrow-suspicious"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="4"
              markerHeight="4"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#EF4444" />
            </marker>
          </defs>

          {/* Edges */}
          {mockLinkedEdges.map((edge, i) => {
            const sNode = mockLinkedNodes.find((n) => n.id === edge.source);
            const tNode = mockLinkedNodes.find((n) => n.id === edge.target);
            if (!sNode || !tNode) return null;

            return (
              <g key={i}>
                <line
                  x1={sNode.x}
                  y1={sNode.y}
                  x2={tNode.x}
                  y2={tNode.y}
                  stroke={edge.suspicious ? '#EF4444' : '#94A3B8'}
                  strokeWidth={edge.suspicious ? 2 : 1.2}
                  strokeDasharray={edge.suspicious ? '4,4' : 'none'}
                  opacity={0.8}
                />
              </g>
            );
          })}

          {/* Nodes */}
          {mockLinkedNodes.map((node) => {
            const isSelected = selectedNode?.id === node.id;
            let fill = '#FFFFFF';
            let stroke = '#6D28D9';

            if (node.type === 'college') {
              fill = node.status === 'critical' ? '#FEE2E2' : '#EDE9FE';
              stroke = node.status === 'critical' ? '#DC2626' : '#7C3AED';
            } else if (node.type === 'trust') {
              fill = '#FEF3C7';
              stroke = '#D97706';
            } else if (node.type === 'person') {
              fill = node.status === 'critical' ? '#FFE4E6' : '#E0E7FF';
              stroke = node.status === 'critical' ? '#E11D48' : '#4F46E5';
            }

            return (
              <g
                key={node.id}
                onClick={() => setSelectedNode(node)}
                className="cursor-pointer transition-transform hover:scale-110"
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={isSelected ? 18 : 14}
                  fill={fill}
                  stroke={stroke}
                  strokeWidth={isSelected ? 3 : 1.5}
                  className="filter drop-shadow-xs"
                />
                <text
                  x={node.x}
                  y={node.y + 22}
                  textAnchor="middle"
                  className="text-[9px] font-sans font-semibold fill-stone-700 dark:fill-stone-300 pointer-events-none"
                >
                  {node.label.split(' ')[0]}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Legend Overlay */}
        <div className="absolute top-2 left-2 flex flex-col gap-1 text-[9px] bg-white/90 dark:bg-slate-900/90 p-1.5 rounded-md border border-stone-200 dark:border-slate-800 backdrop-blur-xs font-mono text-stone-500">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            <span>High Risk College</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span>Trust Entity</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-purple-500" />
            <span>Duplicate Faculty</span>
          </div>
        </div>
      </div>

      {/* Selected Node Inspector Detail */}
      {selectedNode && (
        <div className="mt-3 p-3 rounded-xl bg-purple-50/50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-stone-900 dark:text-slate-100 flex items-center gap-1.5">
              {selectedNode.type === 'college' ? (
                <Building2 className="w-3.5 h-3.5 text-purple-600" />
              ) : selectedNode.type === 'trust' ? (
                <Landmark className="w-3.5 h-3.5 text-amber-600" />
              ) : (
                <User className="w-3.5 h-3.5 text-rose-600" />
              )}
              {selectedNode.label}
            </span>
            <span className="text-[10px] font-mono text-stone-400 capitalize">
              {selectedNode.type}
            </span>
          </div>
          <p className="text-[11px] text-stone-600 dark:text-slate-400 mt-1">
            {selectedNode.type === 'person'
              ? 'Flagged for concurrent EPF contributions across 2 colleges under the same trust.'
              : selectedNode.type === 'trust'
              ? 'Holds 4 affiliated institutions across Western Regional Office jurisdiction.'
              : 'Shares trustee roster and registered administrative address.'}
          </p>
        </div>
      )}
    </div>
  );
};
