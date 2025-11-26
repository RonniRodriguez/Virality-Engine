"""
Idea Inc - LLM Client

Client for interacting with LLM APIs (OpenAI, etc.)
Includes fallback to deterministic mutations when LLM is disabled.
"""

import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.utils.logging import get_logger

from .prompts import MutationPrompts, MutationType

logger = get_logger(__name__)

# Try to import OpenAI, but don't fail if not available
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available, using fallback mutations")


class LLMClient:
    """
    Client for LLM operations.
    
    Supports:
    - Idea generation
    - Idea mutation
    - Idea analysis
    - Fallback to deterministic operations when LLM is disabled
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        enabled: bool = False,
    ):
        self.api_key = api_key
        self.model = model
        self.enabled = enabled and OPENAI_AVAILABLE and api_key
        
        if self.enabled:
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info("LLM client initialized", model=model)
        else:
            self.client = None
            logger.info("LLM client disabled, using fallback mutations")
        
        # Simple cache for LLM responses
        self._cache: Dict[str, str] = {}
        self._cache_max_size = 1000
    
    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key for a prompt"""
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def _cache_response(self, prompt: str, response: str) -> None:
        """Cache a response"""
        if len(self._cache) >= self._cache_max_size:
            # Remove oldest entries (simple LRU approximation)
            keys_to_remove = list(self._cache.keys())[:100]
            for key in keys_to_remove:
                del self._cache[key]
        
        key = self._get_cache_key(prompt)
        self._cache[key] = response
    
    def _get_cached_response(self, prompt: str) -> Optional[str]:
        """Get cached response if available"""
        key = self._get_cache_key(prompt)
        return self._cache.get(key)
    
    async def mutate_idea(
        self,
        idea_text: str,
        mutation_type: MutationType,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mutate an idea using LLM or fallback.
        
        Args:
            idea_text: Original idea text
            mutation_type: Type of mutation to apply
            region: Target region for localization
        
        Returns:
            Dictionary with mutated text and metadata
        """
        if self.enabled:
            return await self._llm_mutate(idea_text, mutation_type, region)
        else:
            return self._fallback_mutate(idea_text, mutation_type, region)
    
    async def _llm_mutate(
        self,
        idea_text: str,
        mutation_type: MutationType,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mutate using LLM"""
        prompt = MutationPrompts.get_mutation_prompt(
            mutation_type=mutation_type,
            idea_text=idea_text,
            region=region,
        )
        
        # Check cache
        cached = self._get_cached_response(prompt)
        if cached:
            logger.debug("Using cached mutation response")
            return {
                "text": cached,
                "mutation_type": mutation_type.value,
                "source": "cache",
            }
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": MutationPrompts.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.8,
            )
            
            mutated_text = response.choices[0].message.content.strip()
            
            # Cache response
            self._cache_response(prompt, mutated_text)
            
            logger.info(
                "LLM mutation completed",
                mutation_type=mutation_type.value,
                original_length=len(idea_text),
                mutated_length=len(mutated_text),
            )
            
            return {
                "text": mutated_text,
                "mutation_type": mutation_type.value,
                "source": "llm",
                "model": self.model,
            }
            
        except Exception as e:
            logger.error("LLM mutation failed", error=str(e))
            # Fall back to deterministic mutation
            return self._fallback_mutate(idea_text, mutation_type, region)
    
    def _fallback_mutate(
        self,
        idea_text: str,
        mutation_type: MutationType,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Deterministic fallback mutation"""
        mutated_text = idea_text
        virality_change = 0.0
        emotional_change = 0.0
        
        if mutation_type == MutationType.SIMPLIFY:
            # Truncate and simplify
            words = idea_text.split()
            if len(words) > 10:
                mutated_text = " ".join(words[:10]) + "..."
            mutated_text = f"Simply put: {mutated_text}"
            virality_change = 0.05
            
        elif mutation_type == MutationType.EMOTIONALIZE:
            # Add emotional markers
            emotional_prefixes = [
                "This is incredible: ",
                "You won't believe: ",
                "Amazing discovery: ",
                "Heartwarming: ",
                "Shocking: ",
            ]
            emotional_suffixes = [
                " 💯",
                " 🔥",
                " ❤️",
                " 😮",
                " 🚀",
            ]
            mutated_text = random.choice(emotional_prefixes) + idea_text + random.choice(emotional_suffixes)
            virality_change = 0.03
            emotional_change = 0.1
            
        elif mutation_type == MutationType.LOCALIZE:
            # Add regional marker
            region_markers = {
                "NA": "🇺🇸 ",
                "EU": "🇪🇺 ",
                "ASIA": "🌏 ",
                "LATAM": "🌎 ",
                "AFRICA": "🌍 ",
                "OCEANIA": "🏝️ ",
            }
            marker = region_markers.get(region, "🌐 ")
            mutated_text = f"{marker}{idea_text}"
            virality_change = 0.02
            
        elif mutation_type == MutationType.POLARIZE:
            # Make more divisive
            polarizing_frames = [
                "Hot take: ",
                "Unpopular opinion: ",
                "The truth they don't want you to know: ",
                "Wake up: ",
                "Choose a side: ",
            ]
            mutated_text = random.choice(polarizing_frames) + idea_text
            virality_change = 0.08
            emotional_change = 0.15
            
        elif mutation_type == MutationType.MEMEIFY:
            # Convert to meme format
            meme_formats = [
                f"Nobody:\nAbsolutely nobody:\nThis idea: {idea_text[:50]}",
                f"POV: {idea_text[:80]}",
                f"Me: *exists*\nThis idea: {idea_text[:50]} 💀",
                f"{idea_text[:60]}... and that's facts 🔥",
                f"Imagine not knowing that {idea_text[:70].lower()}",
            ]
            mutated_text = random.choice(meme_formats)
            virality_change = 0.1
            emotional_change = 0.05
            
        else:  # RANDOM
            # Random variation
            variations = [
                f"Consider this: {idea_text}",
                f"What if... {idea_text}",
                f"Here's a thought: {idea_text}",
                f"Plot twist: {idea_text}",
                idea_text + " - think about it.",
            ]
            mutated_text = random.choice(variations)
            virality_change = random.uniform(-0.02, 0.05)
            emotional_change = random.uniform(-0.02, 0.05)
        
        return {
            "text": mutated_text,
            "mutation_type": mutation_type.value,
            "source": "fallback",
            "virality_change": virality_change,
            "emotional_change": emotional_change,
        }
    
    async def generate_idea(
        self,
        topic: str,
        audience: str = "general",
        tone: str = "neutral",
        virality: str = "medium",
    ) -> Dict[str, Any]:
        """
        Generate a new idea.
        
        Args:
            topic: Topic or theme
            audience: Target audience
            tone: Desired tone
            virality: Virality goal
        
        Returns:
            Dictionary with generated idea and metadata
        """
        if self.enabled:
            return await self._llm_generate(topic, audience, tone, virality)
        else:
            return self._fallback_generate(topic, audience, tone, virality)
    
    async def _llm_generate(
        self,
        topic: str,
        audience: str,
        tone: str,
        virality: str,
    ) -> Dict[str, Any]:
        """Generate using LLM"""
        prompt = MutationPrompts.get_generation_prompt(
            topic=topic,
            audience=audience,
            tone=tone,
            virality=virality,
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": MutationPrompts.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.9,
            )
            
            generated_text = response.choices[0].message.content.strip()
            
            logger.info(
                "LLM generation completed",
                topic=topic,
                length=len(generated_text),
            )
            
            return {
                "text": generated_text,
                "topic": topic,
                "audience": audience,
                "source": "llm",
                "model": self.model,
            }
            
        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            return self._fallback_generate(topic, audience, tone, virality)
    
    def _fallback_generate(
        self,
        topic: str,
        audience: str,
        tone: str,
        virality: str,
    ) -> Dict[str, Any]:
        """Deterministic fallback generation"""
        templates = [
            f"Did you know? {topic} is changing everything we thought we knew.",
            f"The future of {topic} is here, and it's not what you expected.",
            f"Why {topic} matters more than ever in today's world.",
            f"Everyone's talking about {topic}. Here's why.",
            f"The hidden truth about {topic} that experts don't want you to know.",
        ]
        
        generated_text = random.choice(templates)
        
        # Adjust based on virality
        if virality == "high":
            generated_text = "🔥 " + generated_text + " Share this!"
        elif virality == "low":
            generated_text = "Interesting thought: " + generated_text
        
        return {
            "text": generated_text,
            "topic": topic,
            "audience": audience,
            "source": "fallback",
        }
    
    async def analyze_idea(self, idea_text: str) -> Dict[str, Any]:
        """
        Analyze an idea for viral potential.
        
        Args:
            idea_text: Idea text to analyze
        
        Returns:
            Dictionary with analysis scores
        """
        if self.enabled:
            return await self._llm_analyze(idea_text)
        else:
            return self._fallback_analyze(idea_text)
    
    async def _llm_analyze(self, idea_text: str) -> Dict[str, Any]:
        """Analyze using LLM"""
        prompt = MutationPrompts.get_analysis_prompt(idea_text)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing viral content. Respond only with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.3,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                analysis = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{[^}]+\}', result_text)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    return self._fallback_analyze(idea_text)
            
            return {
                **analysis,
                "source": "llm",
            }
            
        except Exception as e:
            logger.error("LLM analysis failed", error=str(e))
            return self._fallback_analyze(idea_text)
    
    def _fallback_analyze(self, idea_text: str) -> Dict[str, Any]:
        """Deterministic fallback analysis"""
        # Simple heuristics
        text_lower = idea_text.lower()
        
        # Virality based on length and punctuation
        virality = 0.3
        if len(idea_text) < 100:
            virality += 0.1
        if "!" in idea_text:
            virality += 0.1
        if any(emoji in idea_text for emoji in ["🔥", "💯", "❤️", "😮"]):
            virality += 0.15
        
        # Emotional valence based on keywords
        emotional = 0.5
        emotional_words = ["amazing", "incredible", "shocking", "heartwarming", "devastating"]
        for word in emotional_words:
            if word in text_lower:
                emotional += 0.1
        
        # Complexity based on word count and sentence length
        words = idea_text.split()
        complexity = min(0.8, len(words) / 50)
        
        # Controversy based on polarizing words
        controversy = 0.2
        polarizing_words = ["truth", "lie", "wake up", "they don't want", "unpopular"]
        for word in polarizing_words:
            if word in text_lower:
                controversy += 0.15
        
        return {
            "virality_score": min(1.0, virality),
            "emotional_valence": min(1.0, emotional),
            "complexity": complexity,
            "controversy_level": min(1.0, controversy),
            "shareability": min(1.0, virality * 0.8 + emotional * 0.2),
            "target_demographics": ["general"],
            "source": "fallback",
        }

