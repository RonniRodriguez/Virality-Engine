import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useIdea } from '../../hooks/useIdea';
import { useAI } from '../../hooks/useAI';
import { ArrowLeft, Zap, Sparkles, Loader2, BrainCircuit, Target } from 'lucide-react';

export const IdeaInjection: React.FC = () => {
  const { worldId } = useParams<{ worldId: string }>();
  const navigate = useNavigate();
  const { injectIdea } = useIdea(worldId);
  const { generate, analyze } = useAI();

  // Form State
  const [text, setText] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [virality, setVirality] = useState(0.5);
  const [emotion, setEmotionalValence] = useState(0.5);
  const [initialAdopters, setInitialAdopters] = useState(5);

  // AI Generation State
  const [generationPrompt, setGenerationPrompt] = useState({
    topic: '',
    audience: 'general',
    tone: 'neutral',
    virality: 'medium' as 'low' | 'medium' | 'high',
  });
  const [showAI, setShowAI] = useState(false);

  // Handlers
  const handleAddTag = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      if (!tags.includes(tagInput.trim())) {
        setTags([...tags, tagInput.trim()]);
      }
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  const handleAnalyze = async () => {
    if (!text) return;
    try {
      const analysis = await analyze.mutateAsync({ idea_text: text });
      setVirality(analysis.virality_score);
      setEmotionalValence(analysis.emotional_valence);
      // Could also suggest tags from analysis.target_demographics
    } catch (error) {
      console.error("Analysis failed", error);
    }
  };

  const handleGenerate = async () => {
    try {
      const result = await generate.mutateAsync(generationPrompt);
      setText(result.text);
      // Auto-analyze the generated text
      await handleAnalyze();
      setShowAI(false);
    } catch (error) {
      console.error("Generation failed", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!worldId) return;

    try {
      await injectIdea.mutateAsync({
        world_id: worldId,
        text,
        tags,
        target: {
          age_groups: [], // Default to all for MVP
          interests: tags,
          regions: [],
        },
        virality_score: virality,
        emotional_valence: emotion,
        initial_adopters: initialAdopters,
      });
      navigate(`/worlds/${worldId}`);
    } catch (error) {
      console.error("Injection failed", error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Link to={`/worlds/${worldId}`} className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
          <ArrowLeft className="w-6 h-6" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Zap className="w-6 h-6 text-yellow-400" />
            Inject New Idea
          </h1>
          <p className="text-slate-400">Craft a meme or belief to spread through the simulation</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg">
            <div className="flex justify-between items-center mb-4">
              <label className="block text-sm font-medium text-slate-300">Idea Content</label>
              <button
                type="button"
                onClick={() => setShowAI(!showAI)}
                className="text-xs flex items-center gap-1 text-brand-400 hover:text-brand-300 transition-colors"
              >
                <Sparkles className="w-3 h-3" />
                {showAI ? 'Hide AI Generator' : 'Use AI Generator'}
              </button>
            </div>

            {showAI && (
              <div className="mb-6 p-4 bg-brand-500/10 border border-brand-500/20 rounded-lg space-y-4">
                <h3 className="text-sm font-bold text-brand-400 flex items-center gap-2">
                  <BrainCircuit className="w-4 h-4" /> AI Idea Generator
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">Topic</label>
                    <input
                      type="text"
                      value={generationPrompt.topic}
                      onChange={(e) => setGenerationPrompt({ ...generationPrompt, topic: e.target.value })}
                      className="input-field w-full text-sm"
                      placeholder="e.g. Cats, Politics"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">Tone</label>
                    <input
                      type="text"
                      value={generationPrompt.tone}
                      onChange={(e) => setGenerationPrompt({ ...generationPrompt, tone: e.target.value })}
                      className="input-field w-full text-sm"
                      placeholder="e.g. Satirical"
                    />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleGenerate}
                  disabled={generate.isPending || !generationPrompt.topic}
                  className="w-full btn-primary py-2 text-sm flex justify-center items-center gap-2"
                >
                  {generate.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate Idea'}
                </button>
              </div>
            )}

            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="input-field w-full h-32 resize-none text-lg mb-2"
              placeholder="Enter your idea text here..."
            />
            
            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={analyze.isPending || !text}
                className="text-xs flex items-center gap-1 text-slate-400 hover:text-white transition-colors"
              >
                {analyze.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Target className="w-3 h-3" />}
                Analyze Virality
              </button>
            </div>
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg">
            <h3 className="text-sm font-medium text-slate-300 mb-4">Targeting & Tags</h3>
            
            <div className="mb-4">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleAddTag}
                className="input-field w-full"
                placeholder="Add tags (press Enter)..."
              />
            </div>
            
            <div className="flex flex-wrap gap-2">
              {tags.map(tag => (
                <span key={tag} className="px-3 py-1 bg-slate-700 rounded-full text-sm text-slate-200 flex items-center gap-2">
                  #{tag}
                  <button onClick={() => removeTag(tag)} className="hover:text-red-400">
                    &times;
                  </button>
                </span>
              ))}
              {tags.length === 0 && <span className="text-slate-500 text-sm italic">No tags added</span>}
            </div>
          </div>
        </div>

        {/* Sidebar Controls */}
        <div className="space-y-6">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg space-y-6">
            <h3 className="font-bold text-white border-b border-slate-700 pb-2">Simulation Parameters</h3>
            
            <div>
              <div className="flex justify-between text-sm mb-2">
                <label className="text-slate-300">Virality Score</label>
                <span className="text-brand-400 font-mono">{virality.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={virality}
                onChange={(e) => setVirality(parseFloat(e.target.value))}
                className="w-full accent-brand-500"
              />
              <p className="text-xs text-slate-500 mt-1">Higher = spreads faster</p>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <label className="text-slate-300">Emotional Valence</label>
                <span className="text-brand-400 font-mono">{emotion.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={emotion}
                onChange={(e) => setEmotionalValence(parseFloat(e.target.value))}
                className="w-full accent-brand-500"
              />
              <p className="text-xs text-slate-500 mt-1">Higher = stronger reaction</p>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <label className="text-slate-300">Initial Adopters</label>
                <span className="text-brand-400 font-mono">{initialAdopters}</span>
              </div>
              <input
                type="number"
                min="1"
                max="100"
                value={initialAdopters}
                onChange={(e) => setInitialAdopters(parseInt(e.target.value))}
                className="input-field w-full"
              />
              <p className="text-xs text-slate-500 mt-1">Seed agents to infect</p>
            </div>

            <button
              onClick={handleSubmit}
              disabled={injectIdea.isPending || !text}
              className="w-full btn-primary py-3 flex justify-center items-center gap-2 mt-4"
            >
              {injectIdea.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
              Launch Idea
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
