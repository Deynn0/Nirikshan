import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { Network, Filter, ZoomIn, ZoomOut, RotateCcw, AlertTriangle, ShieldAlert, Info, Layers } from 'lucide-react';
import { useFraudGraph } from '../../api/hooks';

interface SelectedNodeInfo {
  id: string;
  label: string;
  type: string;
  cluster: number;
  severity: string;
  riskDetails?: string;
  degree?: number;
}

export const IntegrityNetwork: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const { data: fraudGraphData, isLoading } = useFraudGraph();

  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [selectedNode, setSelectedNode] = useState<SelectedNodeInfo | null>(null);

  // Default rich graph data for cross-application fraud detection
  const graphElements = React.useMemo(() => {
    if (fraudGraphData?.elements) {
      const nodes = (fraudGraphData.elements as any).nodes || [];
      const edges = (fraudGraphData.elements as any).edges || [];
      if (nodes.length > 0) {
        return [...nodes, ...edges];
      }
    }
    // High-fidelity fallback graph showing cross-application fraud rings
    return [
      // Cluster 1 (Ghost Faculty Ring)
      { data: { id: 'inst-1', label: 'Delhi Tech Institute', type: 'INSTITUTION', cluster: 1, severity: 'CRITICAL', desc: 'Private Engineering College (Delhi)' } },
      { data: { id: 'inst-2', label: 'Haryana Engg Academy', type: 'INSTITUTION', cluster: 1, severity: 'CRITICAL', desc: 'Affiliated Technical Campus (Gurugram)' } },
      { data: { id: 'fac-101', label: 'Dr. R. Sharma (Hash: 9a8f..)', type: 'FACULTY', cluster: 1, severity: 'CRITICAL', desc: 'Overlapping full-time appointment at 2 institutions' } },
      { data: { id: 'fac-102', label: 'Dr. V. Gupta (Hash: e41b..)', type: 'FACULTY', cluster: 1, severity: 'HIGH', desc: 'Full-time tenure claimed simultaneously' } },
      
      // Edges for Cluster 1
      { data: { id: 'e1', source: 'inst-1', target: 'fac-101', label: 'DECLARED_FACULTY', severity: 'CRITICAL' } },
      { data: { id: 'e2', source: 'inst-2', target: 'fac-101', label: 'DUPLICATE_CLAIM', severity: 'CRITICAL' } },
      { data: { id: 'e3', source: 'inst-1', target: 'fac-102', label: 'DECLARED_FACULTY', severity: 'HIGH' } },
      { data: { id: 'e4', source: 'inst-2', target: 'fac-102', label: 'DUPLICATE_CLAIM', severity: 'HIGH' } },

      // Cluster 2 (Document & Certificate Sharing Ring)
      { data: { id: 'inst-3', label: 'Rajasthan Institute of Science', type: 'INSTITUTION', cluster: 2, severity: 'HIGH', desc: 'Polytechnic applicant' } },
      { data: { id: 'doc-fire-01', label: 'Fire NOC #FS-8812', type: 'CERTIFICATE', cluster: 2, severity: 'HIGH', desc: 'Identical Certificate number used across two distant districts' } },
      { data: { id: 'doc-land-02', label: 'Survey Deed Plot 12-B', type: 'DOCUMENT', cluster: 2, severity: 'MEDIUM', desc: 'Land registration overlap claimed' } },
      { data: { id: 'inst-4', label: 'Jaipur Polytechnic', type: 'INSTITUTION', cluster: 2, severity: 'HIGH', desc: 'Diploma institution' } },

      // Edges for Cluster 2
      { data: { id: 'e5', source: 'inst-3', target: 'doc-fire-01', label: 'SUBMITTED_NOC', severity: 'HIGH' } },
      { data: { id: 'e6', source: 'inst-4', target: 'doc-fire-01', label: 'SHARED_NOC_FRAUD', severity: 'CRITICAL' } },
      { data: { id: 'e7', source: 'inst-3', target: 'doc-land-02', label: 'SUBMITTED_DEED', severity: 'MEDIUM' } },

      // Cluster 3 (Clean Compliant Campus)
      { data: { id: 'inst-5', label: 'IIT Delhi Campus', type: 'INSTITUTION', cluster: 3, severity: 'LOW', desc: 'Fully verified national institution' } },
      { data: { id: 'doc-crypto-01', label: 'DSig Signed Deed 2026', type: 'DOCUMENT', cluster: 3, severity: 'LOW', desc: 'Cryptographically certified' } },
      { data: { id: 'e8', source: 'inst-5', target: 'doc-crypto-01', label: 'VALID_CREDENTIAL', severity: 'LOW' } },
    ];
  }, [fraudGraphData]);

  // Cluster colors
  const clusterColors: Record<number, string> = {
    1: '#f43f5e', // Rose / Red for Ghost Faculty ring
    2: '#f59e0b', // Amber for Certificate Sharing
    3: '#10b981', // Emerald for Compliant
    4: '#8b5cf6', // Purple
  };

  useEffect(() => {
    if (!containerRef.current) return;

    // Filter elements according to severity
    const elementsArray = Array.isArray(graphElements) ? graphElements : [];
    const filteredElements = elementsArray.filter((el: any) => {
      if (severityFilter === 'ALL') return true;
      return el.data?.severity === severityFilter;
    });

    // Also include incident edges if both source and target exist
    const nodeIds = new Set(
      filteredElements
        .filter((el: any) => !('source' in (el.data || {})))
        .map((el: any) => el.data?.id)
    );
    const validElements = filteredElements.filter((el: any) => {
      if ('source' in (el.data || {}) && 'target' in (el.data || {})) {
        return nodeIds.has(el.data.source) && nodeIds.has(el.data.target);
      }
      return true;
    });

    const cy = cytoscape({
      container: containerRef.current,
      elements: validElements as any,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'font-size': '11px',
            'font-family': 'Plus Jakarta Sans, sans-serif',
            'color': '#f8fafc',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'background-color': (ele: any) => {
              const cl = ele.data('cluster') || 1;
              return clusterColors[cl] || '#64748b';
            },
            'border-width': 2,
            'border-color': '#ffffff',
            'border-opacity': 0.8,
            'width': (ele: any) => (ele.data('type') === 'INSTITUTION' ? 44 : 32),
            'height': (ele: any) => (ele.data('type') === 'INSTITUTION' ? 44 : 32),
            'text-outline-color': '#0b0f19',
            'text-outline-width': 2,
          } as any,
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#38bdf8',
          } as any,
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': (ele: any) => {
              const sev = ele.data('severity');
              if (sev === 'CRITICAL') return '#f43f5e';
              if (sev === 'HIGH') return '#f59e0b';
              return '#475569';
            },
            'target-arrow-color': (ele: any) => {
              const sev = ele.data('severity');
              if (sev === 'CRITICAL') return '#f43f5e';
              if (sev === 'HIGH') return '#f59e0b';
              return '#475569';
            },
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '8px',
            'color': '#94a3b8',
            'text-rotation': 'autorotate',
            'text-margin-y': -6,
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        padding: 30,
        componentSpacing: 60,
      } as any,
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode({
        id: node.id(),
        label: node.data('label'),
        type: node.data('type') || 'NODE',
        cluster: node.data('cluster') || 1,
        severity: node.data('severity') || 'MEDIUM',
        riskDetails: node.data('desc') || 'Cross-application graph entity',
        degree: node.degree(),
      });
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [graphElements, severityFilter]);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      {/* Graph Area */}
      <div className="lg:col-span-8 glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl space-y-4">
        {/* Controls Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Integrity Network (Cytoscape.js)
                <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-500/30 font-mono">
                  Cross-Application Fraud Detection
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Detects Ghost Faculty sharing, forged Fire NOC recycling, and collateral collusion across state institutions.
              </p>
            </div>
          </div>

          {/* Filtering by Severity */}
          <div className="flex items-center gap-2">
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs">
              {(['ALL', 'CRITICAL', 'HIGH', 'LOW'] as const).map((sev) => (
                <button
                  key={sev}
                  type="button"
                  onClick={() => setSeverityFilter(sev)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-bold transition-all ${
                    severityFilter === sev
                      ? sev === 'CRITICAL'
                        ? 'bg-rose-600 text-white shadow'
                        : sev === 'HIGH'
                        ? 'bg-amber-600 text-white shadow'
                        : 'bg-sky-600 text-white shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>

            {/* Zoom / Reset */}
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5">
              <button
                type="button"
                onClick={handleZoomIn}
                className="p-1.5 text-slate-300 hover:text-white"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={handleZoomOut}
                className="p-1.5 text-slate-300 hover:text-white"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={handleFit}
                className="p-1.5 text-slate-300 hover:text-white"
                title="Reset View"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Cytoscape Canvas Container */}
        <div
          ref={containerRef}
          className="w-full h-[520px] bg-slate-950 rounded-xl border border-slate-800/80 relative overflow-hidden"
        />

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-rose-500"></span>
              Cluster 1: Ghost Faculty Ring
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-amber-500"></span>
              Cluster 2: Certificate NOC Sharing
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
              Cluster 3: Verified Compliant
            </span>
          </div>
          <span className="font-mono text-[11px] text-slate-500">COSE Force-Directed Layout</span>
        </div>
      </div>

      {/* Node Details Drawer Panel */}
      <div className="lg:col-span-4 glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl space-y-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Info className="w-4 h-4 text-sky-400" />
          <span>Graph Entity Inspection</span>
        </h4>

        {selectedNode ? (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5">
              <div className="flex items-start justify-between gap-2">
                <span className="text-sm font-bold text-white">{selectedNode.label}</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    selectedNode.severity === 'CRITICAL'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      : selectedNode.severity === 'HIGH'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  }`}
                >
                  {selectedNode.severity}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
                <div>
                  <span className="text-slate-500">Entity Type:</span>
                  <p className="text-slate-200 font-bold">{selectedNode.type}</p>
                </div>
                <div>
                  <span className="text-slate-500">Cluster ID:</span>
                  <p className="text-slate-200 font-bold">Cluster #{selectedNode.cluster}</p>
                </div>
                <div>
                  <span className="text-slate-500">Network Degree:</span>
                  <p className="text-slate-200">{selectedNode.degree || 2} Connected Edges</p>
                </div>
                <div>
                  <span className="text-slate-500">System Entity ID:</span>
                  <p className="text-sky-300 truncate">{selectedNode.id}</p>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 text-xs">
                <span className="text-slate-400 font-medium">Risk & Forensic Findings:</span>
                <p className="text-slate-300 mt-1 leading-relaxed bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-sans">
                  {selectedNode.riskDetails}
                </p>
              </div>
            </div>

            {/* Quick Action */}
            <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/30 text-xs space-y-2">
              <div className="flex items-center gap-1.5 text-rose-300 font-bold">
                <ShieldAlert className="w-4 h-4" />
                <span>Statutory AICTE Advisory Flag</span>
              </div>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                This entity is linked to multi-institution cross-filings. Scrutiny officers must verify biometric / Aadhaar UID seed with parent registrar.
              </p>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl space-y-2">
            <Network className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-xs font-medium text-slate-300">No Entity Selected</div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Click any node in the graph (Institution, Faculty Hash, or Certificate) to inspect cross-application relationships and collusion indicators.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
