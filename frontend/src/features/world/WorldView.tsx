import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useWorld } from '../../hooks/useWorld';
import { Play, Pause, ArrowLeft, Users, Activity, Share2, Zap } from 'lucide-react';
import { SimulationStats } from '../simulation/SimulationStats';

export const WorldView: React.FC = () => {
  const { worldId } = useParams<{ worldId: string }>();
  const { world, snapshot, start, stop } = useWorld(worldId!);

  if (world.isLoading) {
    return <div className="flex items-center justify-center h-full text-white">Loading world...</div>;
  }

  if (!world.data) {
    return <div className="text-white">World not found</div>;
  }

  const isRunning = world.data.status === 'running';

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between bg-slate-800/50 p-4 rounded-xl border border-slate-700">
        <div className="flex items-center gap-4">
          <Link to="/worlds" className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-white">{world.data.name}</h1>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                isRunning ? 'bg-green-500/10 text-green-400' : 'bg-slate-700 text-slate-400'
              }`}>
                {world.data.status.toUpperCase()}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-400 mt-1">
              <span className="flex items-center gap-1">
                <Activity className="w-3 h-3" /> Step {snapshot.data?.step || world.data.current_step}
              </span>
              <span className="flex items-center gap-1">
                <Users className="w-3 h-3" /> {snapshot.data?.total_agents || world.data.agent_count} Agents
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!isRunning ? (
            <button
              onClick={() => start.mutate()}
              className="btn-primary flex items-center gap-2"
            >
              <Play className="w-4 h-4" /> Start Simulation
            </button>
          ) : (
            <button
              onClick={() => stop.mutate()}
              className="btn-secondary flex items-center gap-2 border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/10"
            >
              <Pause className="w-4 h-4" /> Pause
            </button>
          )}
          
          <Link 
            to={`/worlds/${worldId}/inject`}
            className="btn-secondary flex items-center gap-2 border-brand-500/50 text-brand-400 hover:bg-brand-500/10"
          >
            <Zap className="w-4 h-4" /> Inject Idea
          </Link>
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        
        {/* Left Column: Visualization (Placeholder for now) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden relative group">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <Share2 className="w-12 h-12 text-slate-700 mx-auto mb-4" />
              <p className="text-slate-500 font-medium">Network Visualization</p>
              <p className="text-slate-600 text-sm">Agent interactions will appear here</p>
            </div>
          </div>
          
          {/* Grid overlay effect */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:24px_24px] opacity-20 pointer-events-none"></div>
        </div>

        {/* Right Column: Stats & Live Feed */}
        <div className="flex flex-col gap-6 min-h-0 overflow-y-auto">
          
          {/* Real-time Metrics */}
          <SimulationStats snapshot={snapshot.data} />

          {/* Event Feed */}
          <div className="flex-1 bg-slate-800/50 rounded-xl border border-slate-700 p-4 flex flex-col min-h-[300px]">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-brand-400" />
              Live Event Stream
            </h3>
            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
              {/* Mock events for now, will connect to websocket later */}
              {snapshot.data?.idea_stats.slice(0, 5).map((idea) => (
                <div key={idea.idea_id} className="text-sm border-l-2 border-brand-500 pl-3 py-1">
                  <p className="text-slate-300">
                    <span className="text-brand-400 font-medium">Spread:</span> "{idea.text.substring(0, 30)}..."
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                     Reached {idea.reach} agents (+{idea.adopters} adopted)
                  </p>
                </div>
              ))}
              {(!snapshot.data || snapshot.data.idea_stats.length === 0) && (
                <p className="text-slate-600 text-sm text-center py-8">
                  No events recorded yet. Start the simulation or inject an idea.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
