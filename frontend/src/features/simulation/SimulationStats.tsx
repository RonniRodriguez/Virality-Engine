import React from 'react';
import { 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';
import type { WorldSnapshot } from '../../types/world';

interface SimulationStatsProps {
  snapshot?: WorldSnapshot;
}

export const SimulationStats: React.FC<SimulationStatsProps> = ({ snapshot }) => {
  if (!snapshot) {
    return <div className="text-slate-500">Waiting for simulation data...</div>;
  }

  const regionalData = Object.entries(snapshot.regional_stats).map(([region, stats]) => ({
    name: region,
    ...stats
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
          <h4 className="text-sm font-medium text-slate-400 mb-4">Population Saturation</h4>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={regionalData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }}
                  itemStyle={{ color: '#f1f5f9' }}
                />
                <Bar dataKey="active_agents" fill="#0ea5e9" name="Active Agents" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
          <h4 className="text-sm font-medium text-slate-400 mb-4">Idea Performance</h4>
          <div className="space-y-3 overflow-y-auto h-48 pr-2">
            {snapshot.idea_stats.map((idea) => (
              <div key={idea.idea_id} className="flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-slate-300 truncate">{idea.text}</span>
                    <span className="text-xs text-brand-400">{(idea.adoption_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-brand-500 rounded-full transition-all duration-500"
                      style={{ width: `${idea.adoption_rate * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
