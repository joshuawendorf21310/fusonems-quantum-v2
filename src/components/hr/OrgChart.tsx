'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight, User, Mail, Phone, Users } from 'lucide-react';

export interface OrgChartNode {
  id: string;
  name: string;
  position: string;
  email?: string;
  phone?: string;
  avatar?: string;
  department?: string;
  children?: OrgChartNode[];
}

interface OrgChartProps {
  data: OrgChartNode;
  onNodeClick?: (node: OrgChartNode) => void;
  className?: string;
}

interface NodeProps {
  node: OrgChartNode;
  onNodeClick?: (node: OrgChartNode) => void;
  level: number;
}

const OrgChartNodeComponent: React.FC<NodeProps> = ({ node, onNodeClick, level }) => {
  const [isExpanded, setIsExpanded] = useState(level < 2);
  const [showTooltip, setShowTooltip] = useState(false);

  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className="flex flex-col items-center">
      <div className="relative">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          whileHover={{ scale: 1.05 }}
          className="relative bg-white rounded-xl shadow-lg p-4 cursor-pointer border-2 border-blue-100 hover:border-blue-400 transition-colors min-w-[240px]"
          onClick={() => onNodeClick?.(node)}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <div className="flex items-center gap-3">
            <div className="relative">
              {node.avatar ? (
                <img
                  src={node.avatar}
                  alt={node.name}
                  className="w-12 h-12 rounded-full object-cover ring-2 ring-blue-500"
                />
              ) : (
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <User className="w-6 h-6 text-white" />
                </div>
              )}
              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 truncate">{node.name}</h3>
              <p className="text-sm text-gray-600 truncate">{node.position}</p>
              {node.department && (
                <p className="text-xs text-gray-500 truncate">{node.department}</p>
              )}
            </div>
          </div>

          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              className="absolute -bottom-3 left-1/2 transform -translate-x-1/2 bg-blue-500 hover:bg-blue-600 text-white rounded-full p-1 shadow-lg transition-colors"
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          )}
        </motion.div>

        <AnimatePresence>
          {showTooltip && (node.email || node.phone) && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute z-50 top-full mt-2 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white rounded-lg shadow-xl p-3 min-w-[200px]"
            >
              <div className="space-y-2">
                {node.email && (
                  <div className="flex items-center gap-2 text-xs">
                    <Mail className="w-3 h-3 text-blue-400" />
                    <span className="truncate">{node.email}</span>
                  </div>
                )}
                {node.phone && (
                  <div className="flex items-center gap-2 text-xs">
                    <Phone className="w-3 h-3 text-green-400" />
                    <span>{node.phone}</span>
                  </div>
                )}
              </div>
              <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {hasChildren && isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="relative mt-8"
          >
            <div className="absolute top-0 left-1/2 w-px h-8 bg-blue-300 -translate-y-8" />
            <div className="flex gap-8 relative">
              {node.children!.map((child, index) => (
                <div key={child.id} className="relative">
                  {index === 0 && node.children!.length > 1 && (
                    <div className="absolute top-0 left-0 right-0 h-px bg-blue-300 -translate-y-8" style={{ left: '50%', right: `${-100 * (node.children!.length - 1)}%` }} />
                  )}
                  <div className="absolute top-0 left-1/2 w-px h-8 bg-blue-300 -translate-y-8" />
                  <OrgChartNodeComponent
                    node={child}
                    onNodeClick={onNodeClick}
                    level={level + 1}
                  />
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const OrgChart: React.FC<OrgChartProps> = ({ data, onNodeClick, className = '' }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const handleWheel = (e: WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY * -0.001;
    const newZoom = Math.min(Math.max(0.5, zoom + delta), 2);
    setZoom(newZoom);
  };

  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener('wheel', handleWheel, { passive: false });
      return () => container.removeEventListener('wheel', handleWheel);
    }
  }, [zoom]);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === containerRef.current || (e.target as HTMLElement).closest('.org-chart-canvas')) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className={`relative bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl shadow-xl overflow-hidden ${className}`}>
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        <button
          onClick={() => setZoom(Math.min(zoom + 0.1, 2))}
          className="bg-white rounded-lg shadow-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          aria-label="Zoom in"
        >
          +
        </button>
        <button
          onClick={() => setZoom(Math.max(zoom - 0.1, 0.5))}
          className="bg-white rounded-lg shadow-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          aria-label="Zoom out"
        >
          -
        </button>
        <button
          onClick={resetView}
          className="bg-white rounded-lg shadow-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          aria-label="Reset view"
        >
          Reset
        </button>
      </div>

      <div className="absolute top-4 left-4 z-10 bg-white rounded-lg shadow-lg px-4 py-2">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Users className="w-4 h-4 text-blue-500" />
          <span className="font-medium">Zoom: {Math.round(zoom * 100)}%</span>
        </div>
      </div>

      <div
        ref={containerRef}
        className="org-chart-canvas h-[600px] overflow-hidden cursor-move"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <div
          className="flex items-start justify-center p-8 min-h-full"
          style={{
            transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
            transformOrigin: 'center',
            transition: isDragging ? 'none' : 'transform 0.2s ease-out',
          }}
        >
          <OrgChartNodeComponent node={data} onNodeClick={onNodeClick} level={0} />
        </div>
      </div>
    </div>
  );
};

export default OrgChart;
