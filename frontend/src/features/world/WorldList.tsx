import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useWorlds } from '../../hooks/useWorld';
import { Plus, Globe, Users, Activity, PlayCircle } from 'lucide-react';
import { CreateWorldModal } from './CreateWorldModal';

export const WorldList: React.FC = () => {
  const { worlds } = useWorlds();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  if (worlds.isLoading) {
    return <div className="text-white">Loading worlds...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Simulation Worlds</h1>
          <p className="text-slate-400">Manage and monitor your social simulations</p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Create World
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {worlds.data?.map((world) => (
          <Link
            key={world.id}
            to={`/worlds/${world.id}`}
            className="card hover:border-brand-500/50 transition-colors group"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="p-2 bg-brand-500/10 rounded-lg text-brand-400 group-hover:text-brand-300 group-hover:bg-brand-500/20 transition-colors">
                <Globe className="w-6 h-6" />
              </div>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                world.status === 'running' 
                  ? 'bg-green-500/10 text-green-400' 
                  : 'bg-slate-700 text-slate-400'
              }`}>
                {world.status.toUpperCase()}
              </span>
            </div>

            <h3 className="text-xl font-bold text-white mb-2">{world.name}</h3>
            <p className="text-slate-400 text-sm mb-4 line-clamp-2">
              {world.description || 'No description provided.'}
            </p>

            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-700">
              <div>
                <div className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                  <Users className="w-3 h-3" /> Agents
                </div>
                <div className="font-mono text-white">{world.agent_count.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                  <Activity className="w-3 h-3" /> Step
                </div>
                <div className="font-mono text-white">{world.current_step.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                  <PlayCircle className="w-3 h-3" /> Ideas
                </div>
                <div className="font-mono text-white">{world.idea_count}</div>
              </div>
            </div>
          </Link>
        ))}

        {worlds.data?.length === 0 && (
          <div className="col-span-full text-center py-12 bg-slate-800/50 rounded-xl border border-slate-800 border-dashed">
            <Globe className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">No worlds found</h3>
            <p className="text-slate-400 mb-6">Start your first simulation experiment today.</p>
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="btn-primary inline-flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Create World
            </button>
          </div>
        )}
      </div>

      {isCreateModalOpen && (
        <CreateWorldModal onClose={() => setIsCreateModalOpen(false)} />
      )}
    </div>
  );
};

