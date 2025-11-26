"""
Idea Inc - LLM Prompts

Prompt templates for idea generation and mutation.
"""

from enum import Enum
from typing import Dict, List, Optional


class MutationType(str, Enum):
    """Types of idea mutations"""
    SIMPLIFY = "simplify"
    EMOTIONALIZE = "emotionalize"
    LOCALIZE = "localize"
    POLARIZE = "polarize"
    MEMEIFY = "memeify"
    RANDOM = "random"


class MutationPrompts:
    """Prompt templates for idea mutation"""
    
    SYSTEM_PROMPT = """You are an AI assistant specialized in analyzing and transforming ideas/memes for a social simulation platform. Your task is to create variations of ideas that would spread differently through a population.

Guidelines:
- Keep outputs concise (under 200 characters for memes, under 500 for ideas)
- Maintain the core concept while applying the requested transformation
- Consider how the variation might appeal to different demographics
- Be creative but appropriate
- Do not generate harmful, illegal, or explicitly offensive content

Output only the transformed idea text, nothing else."""

    MUTATION_PROMPTS: Dict[MutationType, str] = {
        MutationType.SIMPLIFY: """Transform this idea to be simpler and more accessible:
- Use shorter words and sentences
- Remove jargon and complex concepts
- Make it easy to understand at a glance
- Aim for a 6th grade reading level

Original idea: {idea_text}

Simplified version:""",

        MutationType.EMOTIONALIZE: """Transform this idea to have stronger emotional appeal:
- Add emotional language and imagery
- Appeal to feelings like hope, fear, excitement, or nostalgia
- Make it more personally relatable
- Use vivid, evocative words

Original idea: {idea_text}

Emotionalized version:""",

        MutationType.LOCALIZE: """Adapt this idea for the {region} region:
- Use culturally relevant references
- Adapt language and tone for local sensibilities
- Consider regional values and concerns
- Make it feel locally relevant

Original idea: {idea_text}

Localized version for {region}:""",

        MutationType.POLARIZE: """Transform this idea to be more polarizing:
- Make it take a stronger stance
- Create a clearer us-vs-them framing
- Emphasize controversy or debate
- Make people want to share their opinion

Original idea: {idea_text}

Polarized version:""",

        MutationType.MEMEIFY: """Transform this idea into a meme format:
- Make it catchy and shareable
- Use humor if appropriate
- Add relevant emoji or formatting hints
- Make it quotable and memorable
- Keep it under 100 characters if possible

Original idea: {idea_text}

Meme version:""",

        MutationType.RANDOM: """Create an interesting variation of this idea:
- Change the framing or perspective
- Add a twist or unexpected element
- Make it more engaging or surprising
- Keep the core concept but present it differently

Original idea: {idea_text}

Variation:""",
    }

    GENERATION_PROMPT = """Generate an original idea/meme based on these parameters:

Topic/Theme: {topic}
Target audience: {audience}
Desired tone: {tone}
Virality goal: {virality} (low/medium/high)

Create a concise, engaging idea that would spread well among the target audience.

Generated idea:"""

    ANALYSIS_PROMPT = """Analyze this idea for its viral potential:

Idea: {idea_text}

Provide a JSON response with these scores (0.0 to 1.0):
{{
    "virality_score": <how likely to spread>,
    "emotional_valence": <emotional intensity>,
    "complexity": <how complex/nuanced>,
    "controversy_level": <how controversial>,
    "shareability": <how likely to be shared>,
    "target_demographics": [<list of likely target groups>]
}}

Analysis:"""

    @classmethod
    def get_mutation_prompt(
        cls,
        mutation_type: MutationType,
        idea_text: str,
        region: Optional[str] = None,
    ) -> str:
        """
        Get the prompt for a specific mutation type.
        
        Args:
            mutation_type: Type of mutation to apply
            idea_text: Original idea text
            region: Target region (for localization)
        
        Returns:
            Formatted prompt string
        """
        template = cls.MUTATION_PROMPTS.get(
            mutation_type,
            cls.MUTATION_PROMPTS[MutationType.RANDOM]
        )
        
        return template.format(
            idea_text=idea_text,
            region=region or "global",
        )

    @classmethod
    def get_generation_prompt(
        cls,
        topic: str,
        audience: str = "general",
        tone: str = "neutral",
        virality: str = "medium",
    ) -> str:
        """
        Get the prompt for idea generation.
        
        Args:
            topic: Topic or theme for the idea
            audience: Target audience description
            tone: Desired tone (humorous, serious, etc.)
            virality: Desired virality level
        
        Returns:
            Formatted prompt string
        """
        return cls.GENERATION_PROMPT.format(
            topic=topic,
            audience=audience,
            tone=tone,
            virality=virality,
        )

    @classmethod
    def get_analysis_prompt(cls, idea_text: str) -> str:
        """
        Get the prompt for idea analysis.
        
        Args:
            idea_text: Idea text to analyze
        
        Returns:
            Formatted prompt string
        """
        return cls.ANALYSIS_PROMPT.format(idea_text=idea_text)

