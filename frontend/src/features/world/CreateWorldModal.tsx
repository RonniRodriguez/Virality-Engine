import React, { useState } from 'react';
import { useWorlds } from '../../hooks/useWorld';
import { X, Loader2 } from 'lucide-react';

interface CreateWorldModalProps {
  onClose: () => void;
}

export const CreateWorldModal: React.FC<CreateWorldModalProps> = ({ onClose }) => {
  const { createWorld } = useWorlds();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [population, setPopulation] = useState(1000);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createWorld.mutateAsync({
        name,
        description,
        is_public: true,
        config: {
          population_size: population,
          network_type: 'scale_free',
          network_density: 0.1,
          mutation_rate: 0.01,
          decay_rate: 0.001,
          time_step_ms: 100,
        },
      });
      onClose();
    } catch (error) {
      console.error('Failed to create world', error);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl">
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <h2 className="text-xl font-bold text-white">Create New World</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">World Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input-field w-full"
              placeholder="e.g. Viral Meme Lab"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input-field w-full h-24 resize-none"
              placeholder="Describe the purpose of this simulation..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Population Size
            </label>
            <input
              type="number"
              value={population}
              onChange={(e) => setPopulation(Number(e.target.value))}
              className="input-field w-full"
              min={100}
              max={10000}
              step={100}
            />
            <p className="text-xs text-slate-500 mt-1">
              Recommended: 1,000 - 5,000 agents for MVP performance.
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createWorld.isPending}
              className="flex-1 btn-primary flex items-center justify-center gap-2"
            >
              {createWorld.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Create World
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

