'use client';

import React, { useState } from 'react';

export default function AnalyticsDashboard() {
  const [hoveredCell, setHoveredCell] = useState<{ row: number; col: number; location: string; calls: number } | null>(null);

  // Mock data
  const stats = [
    { label: 'Total Calls', value: '12,847', trend: '+12.5%', isUp: true },
    { label: 'Average Response Time', value: '4.2 min', trend: '-8.3%', isUp: true },
    { label: 'Revenue This Month', value: '$847,320', trend: '+18.7%', isUp: true },
    { label: 'Active Units', value: '142', trend: '+5', isUp: true },
  ];

  const responseTimeData = [
    { day: 'Mon', value: 5.2 },
    { day: 'Tue', value: 4.8 },
    { day: 'Wed', value: 4.5 },
    { day: 'Thu', value: 4.2 },
    { day: 'Fri', value: 4.0 },
    { day: 'Sat', value: 4.5 },
    { day: 'Sun', value: 4.2 },
  ];

  const callVolumeByHour = [
    120, 95, 78, 65, 58, 72, 145, 268, 312, 285, 245, 228,
    215, 198, 205, 235, 278, 325, 298, 265, 235, 198, 165, 142
  ];

  const revenueMetrics = [
    { label: 'Collections Rate', value: '94.2%', color: 'orange' },
    { label: 'Average Days to Payment', value: '28 days', color: 'orange' },
    { label: 'Denial Rate', value: '3.8%', color: 'red' },
    { label: 'Write-off Percentage', value: '2.1%', color: 'red' },
  ];

  const heatMapData = [
    [
      { location: 'Downtown', calls: 245 },
      { location: 'Midtown', calls: 189 },
      { location: 'Uptown', calls: 312 },
      { location: 'East Side', calls: 156 },
      { location: 'West Side', calls: 201 },
    ],
    [
      { location: 'North District', calls: 287 },
      { location: 'Central', calls: 423 },
      { location: 'South District', calls: 198 },
      { location: 'Harbor', calls: 134 },
      { location: 'Airport', calls: 267 },
    ],
    [
      { location: 'Suburbs N', calls: 167 },
      { location: 'Suburbs E', calls: 145 },
      { location: 'Suburbs S', calls: 178 },
      { location: 'Suburbs W', calls: 156 },
      { location: 'Industrial', calls: 223 },
    ],
    [
      { location: 'University', calls: 298 },
      { location: 'Medical Dist', calls: 389 },
      { location: 'Financial', calls: 256 },
      { location: 'Tech Hub', calls: 234 },
      { location: 'Retail Zone', calls: 189 },
    ],
  ];

  const predictiveData = [
    { day: 'Mon', predicted: 2850, lower: 2650, upper: 3050 },
    { day: 'Tue', predicted: 2920, lower: 2720, upper: 3120 },
    { day: 'Wed', predicted: 3100, lower: 2900, upper: 3300 },
    { day: 'Thu', predicted: 3050, lower: 2850, upper: 3250 },
    { day: 'Fri', predicted: 2980, lower: 2780, upper: 3180 },
    { day: 'Sat', predicted: 2650, lower: 2450, upper: 2850 },
    { day: 'Sun', predicted: 2580, lower: 2380, upper: 2780 },
  ];

  const topUnits = [
    { name: 'Unit Alpha-7', completionRate: 98.5, calls: 1247 },
    { name: 'Unit Bravo-3', completionRate: 97.8, calls: 1189 },
    { name: 'Unit Charlie-9', completionRate: 96.9, calls: 1156 },
    { name: 'Unit Delta-5', completionRate: 96.2, calls: 1098 },
    { name: 'Unit Echo-1', completionRate: 95.7, calls: 1045 },
    { name: 'Unit Foxtrot-4', completionRate: 95.1, calls: 987 },
    { name: 'Unit Golf-8', completionRate: 94.8, calls: 945 },
    { name: 'Unit Hotel-2', completionRate: 94.3, calls: 912 },
    { name: 'Unit India-6', completionRate: 93.9, calls: 876 },
    { name: 'Unit Juliet-10', completionRate: 93.5, calls: 834 },
  ];

  const maxResponseTime = Math.max(...responseTimeData.map(d => d.value));
  const maxCallVolume = Math.max(...callVolumeByHour);
  const maxPredicted = Math.max(...predictiveData.map(d => d.upper));

  const getHeatColor = (calls: number) => {
    const max = 423;
    const intensity = calls / max;
    if (intensity < 0.3) return '#1a1a1a';
    if (intensity < 0.5) return '#4a1a0a';
    if (intensity < 0.7) return '#f97316';
    return '#ef4444';
  };

  return (
    <div className="analytics-dashboard">
      <style jsx>{`
        .analytics-dashboard {
          min-height: 100vh;
          background: #0f0f0f;
          padding: 2rem;
          color: white;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .header {
          margin-bottom: 3rem;
          animation: fadeIn 0.5s ease-in;
        }

        .header h1 {
          font-size: 2.5rem;
          font-weight: 700;
          background: linear-gradient(135deg, #f97316, #ef4444);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin-bottom: 0.5rem;
        }

        .header p {
          color: #888;
          font-size: 1rem;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
          animation: slideUp 0.6s ease-out;
        }

        .stat-card {
          background: linear-gradient(135deg, #f97316, #ea580c);
          border-radius: 1rem;
          padding: 1.5rem;
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          cursor: pointer;
        }

        .stat-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 30px rgba(249, 115, 22, 0.3);
        }

        .stat-label {
          font-size: 0.875rem;
          color: rgba(255, 255, 255, 0.9);
          margin-bottom: 0.5rem;
          font-weight: 500;
        }

        .stat-value {
          font-size: 2rem;
          font-weight: 700;
          color: white;
          margin-bottom: 0.5rem;
        }

        .stat-trend {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.875rem;
          color: rgba(255, 255, 255, 0.95);
        }

        .chart-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
          gap: 2rem;
          margin-bottom: 2rem;
        }

        .chart-card {
          background: #1a1a1a;
          border-radius: 1rem;
          padding: 1.5rem;
          border: 1px solid #2a2a2a;
          animation: fadeIn 0.7s ease-in;
        }

        .chart-title {
          font-size: 1.25rem;
          font-weight: 600;
          color: #f97316;
          margin-bottom: 1.5rem;
        }

        .line-chart {
          height: 250px;
          position: relative;
          padding: 1rem 0;
        }

        .line-chart svg {
          width: 100%;
          height: 100%;
        }

        .chart-labels {
          display: flex;
          justify-content: space-between;
          margin-top: 0.5rem;
          color: #666;
          font-size: 0.75rem;
        }

        .bar-chart {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          height: 200px;
          gap: 0.25rem;
          padding: 1rem 0;
        }

        .bar {
          flex: 1;
          background: #f97316;
          border-radius: 4px 4px 0 0;
          transition: all 0.3s ease;
          cursor: pointer;
          position: relative;
        }

        .bar:hover {
          background: #ea580c;
          transform: scaleY(1.05);
        }

        .bar-tooltip {
          position: absolute;
          bottom: 100%;
          left: 50%;
          transform: translateX(-50%);
          background: #0a0a0a;
          color: #f97316;
          padding: 0.25rem 0.5rem;
          border-radius: 0.25rem;
          font-size: 0.75rem;
          white-space: nowrap;
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.3s ease;
        }

        .bar:hover .bar-tooltip {
          opacity: 1;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
          animation: slideUp 0.8s ease-out;
        }

        .metric-card {
          background: #1a1a1a;
          border-radius: 1rem;
          padding: 1.5rem;
          border-left: 4px solid;
          transition: transform 0.3s ease;
        }

        .metric-card:hover {
          transform: translateX(5px);
        }

        .metric-card.orange {
          border-color: #f97316;
        }

        .metric-card.red {
          border-color: #ef4444;
        }

        .metric-label {
          font-size: 0.875rem;
          color: #888;
          margin-bottom: 0.5rem;
        }

        .metric-value {
          font-size: 1.75rem;
          font-weight: 700;
          color: white;
        }

        .heatmap-container {
          background: #1a1a1a;
          border-radius: 1rem;
          padding: 1.5rem;
          margin-bottom: 2rem;
          border: 1px solid #2a2a2a;
          animation: fadeIn 0.9s ease-in;
        }

        .heatmap-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 0.5rem;
          margin-top: 1rem;
        }

        .heatmap-cell {
          aspect-ratio: 1;
          border-radius: 0.5rem;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          position: relative;
        }

        .heatmap-cell:hover {
          transform: scale(1.1);
          box-shadow: 0 5px 20px rgba(249, 115, 22, 0.5);
          z-index: 10;
        }

        .heatmap-tooltip {
          position: absolute;
          bottom: 110%;
          left: 50%;
          transform: translateX(-50%);
          background: #0a0a0a;
          color: #f97316;
          padding: 0.5rem 1rem;
          border-radius: 0.5rem;
          font-size: 0.75rem;
          white-space: nowrap;
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.3s ease;
          border: 1px solid #f97316;
          z-index: 20;
        }

        .heatmap-cell:hover .heatmap-tooltip {
          opacity: 1;
        }

        .predictive-card {
          background: #1a1a1a;
          border-radius: 1rem;
          padding: 1.5rem;
          margin-bottom: 2rem;
          border: 1px solid #2a2a2a;
          animation: fadeIn 1s ease-in;
        }

        .predictive-chart {
          height: 200px;
          position: relative;
          margin-top: 1rem;
        }

        .predictive-chart svg {
          width: 100%;
          height: 100%;
        }

        .confidence-label {
          text-align: center;
          color: #666;
          font-size: 0.875rem;
          margin-top: 0.5rem;
        }

        .top-units {
          background: #1a1a1a;
          border-radius: 1rem;
          padding: 1.5rem;
          margin-bottom: 2rem;
          border: 1px solid #2a2a2a;
          animation: fadeIn 1.1s ease-in;
        }

        .unit-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          margin-top: 1rem;
        }

        .unit-item {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1rem;
          background: #0f0f0f;
          border-radius: 0.5rem;
          transition: transform 0.3s ease;
        }

        .unit-item:hover {
          transform: translateX(5px);
          background: #252525;
        }

        .unit-rank {
          font-size: 1.25rem;
          font-weight: 700;
          color: #f97316;
          min-width: 2rem;
        }

        .unit-info {
          flex: 1;
        }

        .unit-name {
          font-weight: 600;
          color: white;
          margin-bottom: 0.25rem;
        }

        .unit-calls {
          font-size: 0.75rem;
          color: #666;
        }

        .unit-progress {
          flex: 1;
          max-width: 200px;
        }

        .progress-bar {
          height: 8px;
          background: #2a2a2a;
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #f97316, #ea580c);
          border-radius: 4px;
          transition: width 0.5s ease;
        }

        .unit-rate {
          font-size: 1rem;
          font-weight: 600;
          color: #f97316;
          min-width: 4rem;
          text-align: right;
        }

        .actions-row {
          display: flex;
          gap: 1rem;
          flex-wrap: wrap;
          animation: fadeIn 1.2s ease-in;
        }

        .action-button {
          background: #f97316;
          color: #0a0a0a;
          border: none;
          padding: 1rem 2rem;
          border-radius: 0.5rem;
          font-weight: 600;
          font-size: 1rem;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .action-button:hover {
          background: #ea580c;
          transform: translateY(-2px);
          box-shadow: 0 5px 20px rgba(249, 115, 22, 0.4);
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @media (max-width: 768px) {
          .analytics-dashboard {
            padding: 1rem;
          }

          .header h1 {
            font-size: 1.75rem;
          }

          .stats-grid,
          .chart-grid,
          .metrics-grid {
            grid-template-columns: 1fr;
          }

          .heatmap-grid {
            grid-template-columns: repeat(3, 1fr);
          }

          .unit-progress {
            max-width: 150px;
          }

          .actions-row {
            flex-direction: column;
          }

          .action-button {
            width: 100%;
          }
        }
      `}</style>

      <div className="header">
        <h1>Advanced Analytics Dashboard</h1>
        <p>Real-time insights and predictive intelligence</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        {stats.map((stat, index) => (
          <div key={index} className="stat-card">
            <div className="stat-label">{stat.label}</div>
            <div className="stat-value">{stat.value}</div>
            <div className="stat-trend">
              <span>{stat.isUp ? '↑' : '↓'}</span>
              <span>{stat.trend}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="chart-grid">
        {/* Response Time Trend */}
        <div className="chart-card">
          <div className="chart-title">Response Time Trend (Last 7 Days)</div>
          <div className="line-chart">
            <svg viewBox="0 0 700 250" preserveAspectRatio="none">
              <defs>
                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#f97316" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#f97316" stopOpacity="0" />
                </linearGradient>
              </defs>
              {/* Grid lines */}
              {[0, 1, 2, 3, 4].map((i) => (
                <line
                  key={i}
                  x1="0"
                  y1={i * 50}
                  x2="700"
                  y2={i * 50}
                  stroke="#2a2a2a"
                  strokeWidth="1"
                />
              ))}
              {/* Area fill */}
              <path
                d={`M 0 ${250 - (responseTimeData[0].value / maxResponseTime) * 200} ${responseTimeData
                  .map((d, i) => `L ${(i / (responseTimeData.length - 1)) * 700} ${250 - (d.value / maxResponseTime) * 200}`)
                  .join(' ')} L 700 250 L 0 250 Z`}
                fill="url(#lineGradient)"
              />
              {/* Line */}
              <path
                d={`M 0 ${250 - (responseTimeData[0].value / maxResponseTime) * 200} ${responseTimeData
                  .map((d, i) => `L ${(i / (responseTimeData.length - 1)) * 700} ${250 - (d.value / maxResponseTime) * 200}`)
                  .join(' ')}`}
                fill="none"
                stroke="#f97316"
                strokeWidth="3"
              />
              {/* Points */}
              {responseTimeData.map((d, i) => (
                <circle
                  key={i}
                  cx={(i / (responseTimeData.length - 1)) * 700}
                  cy={250 - (d.value / maxResponseTime) * 200}
                  r="5"
                  fill="#f97316"
                />
              ))}
            </svg>
          </div>
          <div className="chart-labels">
            {responseTimeData.map((d) => (
              <span key={d.day}>{d.day}</span>
            ))}
          </div>
        </div>

        {/* Call Volume by Hour */}
        <div className="chart-card">
          <div className="chart-title">Call Volume by Hour (24h)</div>
          <div className="bar-chart">
            {callVolumeByHour.map((value, index) => (
              <div
                key={index}
                className="bar"
                style={{ height: `${(value / maxCallVolume) * 100}%` }}
              >
                <div className="bar-tooltip">
                  {index}:00 - {value} calls
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Revenue Cycle Metrics */}
      <div className="metrics-grid">
        {revenueMetrics.map((metric, index) => (
          <div key={index} className={`metric-card ${metric.color}`}>
            <div className="metric-label">{metric.label}</div>
            <div className="metric-value">{metric.value}</div>
          </div>
        ))}
      </div>

      {/* Heat Map */}
      <div className="heatmap-container">
        <div className="chart-title">High Demand Areas - Call Density</div>
        <div className="heatmap-grid">
          {heatMapData.flat().map((cell, index) => (
            <div
              key={index}
              className="heatmap-cell"
              style={{ backgroundColor: getHeatColor(cell.calls) }}
            >
              {cell.calls}
              <div className="heatmap-tooltip">
                {cell.location}: {cell.calls} calls
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Predictive Analytics */}
      <div className="predictive-card">
        <div className="chart-title">Predicted Call Volume - Next Week</div>
        <div className="predictive-chart">
          <svg viewBox="0 0 700 200" preserveAspectRatio="none">
            <defs>
              <linearGradient id="predictGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#f97316" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#f97316" stopOpacity="0" />
              </linearGradient>
            </defs>
            {/* Confidence interval */}
            <path
              d={`M 0 ${200 - (predictiveData[0].lower / maxPredicted) * 180} ${predictiveData
                .map((d, i) => `L ${(i / (predictiveData.length - 1)) * 700} ${200 - (d.lower / maxPredicted) * 180}`)
                .join(' ')} ${predictiveData
                .reverse()
                .map((d, i) => `L ${700 - (i / (predictiveData.length - 1)) * 700} ${200 - (d.upper / maxPredicted) * 180}`)
                .join(' ')} Z`}
              fill="url(#predictGradient)"
            />
            {/* Prediction line */}
            <path
              d={`M 0 ${200 - (predictiveData.reverse()[0].predicted / maxPredicted) * 180} ${predictiveData
                .map((d, i) => `L ${(i / (predictiveData.length - 1)) * 700} ${200 - (d.predicted / maxPredicted) * 180}`)
                .join(' ')}`}
              fill="none"
              stroke="#f97316"
              strokeWidth="3"
              strokeDasharray="5,5"
            />
            {/* Points */}
            {predictiveData.map((d, i) => (
              <circle
                key={i}
                cx={(i / (predictiveData.length - 1)) * 700}
                cy={200 - (d.predicted / maxPredicted) * 180}
                r="5"
                fill="#f97316"
              />
            ))}
          </svg>
        </div>
        <div className="chart-labels">
          {predictiveData.map((d) => (
            <span key={d.day}>{d.day}</span>
          ))}
        </div>
        <div className="confidence-label">95% Confidence Interval</div>
      </div>

      {/* Top Performing Units */}
      <div className="top-units">
        <div className="chart-title">Top Performing Units</div>
        <div className="unit-list">
          {topUnits.map((unit, index) => (
            <div key={index} className="unit-item">
              <div className="unit-rank">#{index + 1}</div>
              <div className="unit-info">
                <div className="unit-name">{unit.name}</div>
                <div className="unit-calls">{unit.calls} calls completed</div>
              </div>
              <div className="unit-progress">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${unit.completionRate}%` }}
                  />
                </div>
              </div>
              <div className="unit-rate">{unit.completionRate}%</div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="actions-row">
        <button className="action-button">Export PDF</button>
        <button className="action-button">Schedule Report</button>
        <button className="action-button">Share Dashboard</button>
      </div>
    </div>
  );
}
