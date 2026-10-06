import React, { useState } from 'react';
import {
  calculateImplied,
  calculateOverround,
  calculateMarginFreeProportional,
  calculateFairOdds
} from '../utils/math';

export const MarginXRay: React.FC = () => {
  const [oddsStr, setOddsStr] = useState({
    home: '1.60',
    draw: '4.20',
    away: '5.50',
  });

  const handleOddsChange = (key: 'home' | 'draw' | 'away', value: string) => {
    setOddsStr((prev) => ({ ...prev, [key]: value }));
  };

  const oddsNum = {
    home: parseFloat(oddsStr.home) || 0,
    draw: parseFloat(oddsStr.draw) || 0,
    away: parseFloat(oddsStr.away) || 0,
  };

  const implied = {
    home: calculateImplied(oddsNum.home),
    draw: calculateImplied(oddsNum.draw),
    away: calculateImplied(oddsNum.away),
  };

  const overround = calculateOverround([implied.home, implied.draw, implied.away]);

  const marginFree = {
    home: calculateMarginFreeProportional(implied.home, overround),
    draw: calculateMarginFreeProportional(implied.draw, overround),
    away: calculateMarginFreeProportional(implied.away, overround),
  };

  const fairOdds = {
    home: calculateFairOdds(marginFree.home),
    draw: calculateFairOdds(marginFree.draw),
    away: calculateFairOdds(marginFree.away),
  };

  const expectedCost = (overround / (1 + overround)) * 100;
  const totalImplied = 1 + overround;

  const formatPct = (val: number) => (val * 100).toFixed(2) + '%';
  const formatOdds = (val: number) => val.toFixed(2);

  return (
    <div className="bg-surface border border-line rounded-[10px] p-8 shadow-sm">
      <h2 className="text-2xl font-bold mb-6">Margin X-Ray</h2>

      {/* Inputs */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div>
          <label className="block text-sm font-medium mb-1 text-muted">Home Odds</label>
          <input
            type="number"
            step="0.01"
            className="w-full bg-background border border-line rounded px-3 py-2 text-text focus:outline-none focus:border-brand"
            value={oddsStr.home}
            onChange={(e) => handleOddsChange('home', e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1 text-muted">Draw Odds</label>
          <input
            type="number"
            step="0.01"
            className="w-full bg-background border border-line rounded px-3 py-2 text-text focus:outline-none focus:border-brand"
            value={oddsStr.draw}
            onChange={(e) => handleOddsChange('draw', e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1 text-muted">Away Odds</label>
          <input
            type="number"
            step="0.01"
            className="w-full bg-background border border-line rounded px-3 py-2 text-text focus:outline-none focus:border-brand"
            value={oddsStr.away}
            onChange={(e) => handleOddsChange('away', e.target.value)}
          />
        </div>
      </div>

      {/* Table */}
      <div className="mb-8 overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-line text-sm text-muted">
              <th className="py-2 font-medium">Outcome</th>
              <th className="py-2 font-medium">Odds</th>
              <th className="py-2 font-medium">Implied</th>
              <th className="py-2 font-medium">Margin-free</th>
              <th className="py-2 font-medium">Fair odds</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-line">
              <td className="py-3 font-medium">Home</td>
              <td className="py-3">{oddsStr.home}</td>
              <td className="py-3">{formatPct(implied.home)}</td>
              <td className="py-3 text-brand">{formatPct(marginFree.home)}</td>
              <td className="py-3 text-brand">{formatOdds(fairOdds.home)}</td>
            </tr>
            <tr className="border-b border-line">
              <td className="py-3 font-medium">Draw</td>
              <td className="py-3">{oddsStr.draw}</td>
              <td className="py-3">{formatPct(implied.draw)}</td>
              <td className="py-3 text-brand">{formatPct(marginFree.draw)}</td>
              <td className="py-3 text-brand">{formatOdds(fairOdds.draw)}</td>
            </tr>
            <tr>
              <td className="py-3 font-medium">Away</td>
              <td className="py-3">{oddsStr.away}</td>
              <td className="py-3">{formatPct(implied.away)}</td>
              <td className="py-3 text-brand">{formatPct(marginFree.away)}</td>
              <td className="py-3 text-brand">{formatOdds(fairOdds.away)}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Bottom Block */}
      <div className="bg-background rounded-lg p-6 border border-line">
        <div className="flex justify-between items-end mb-4">
          <div>
            <div className="text-sm text-muted mb-1">Overround (Bookmaker Margin)</div>
            <div className="text-2xl font-bold">{formatPct(overround)}</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted mb-1">Total Implied</div>
            <div className="text-xl">{formatPct(totalImplied)}</div>
          </div>
        </div>

        {/* Visual Bar */}
        <div className="h-4 w-full bg-line rounded-full overflow-hidden flex mb-4">
          <div className="h-full bg-muted" style={{ width: `${Math.max(0, Math.min(100, (1 / totalImplied) * 100))}%` }}></div>
          <div className="h-full bg-cost" style={{ width: `${Math.max(0, Math.min(100, (overround / totalImplied) * 100))}%` }}></div>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-muted">Fair Market (100%)</span>
          <span className="text-cost font-medium flex items-center gap-2">
            Expected Cost: {expectedCost.toFixed(2)}%
          </span>
        </div>
      </div>
    </div>
  );
};
