"""
AI Service for Moral Duel Platform

Provides AI-powered features:
- Generate moral dilemma cases
- Generate AI verdicts with reasoning
- Moderate user-submitted content
"""
import hashlib
import json
import logging
import os
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from app.config import settings

# Set Gemini API key in environment BEFORE importing Spoon AI
# Spoon AI uses GEMINI_API_KEY env variable for Gemini provider
if settings.GOOGLE_API_KEY and not settings.GOOGLE_API_KEY.startswith("your-"):
    os.environ["GEMINI_API_KEY"] = settings.GOOGLE_API_KEY

from spoon_ai.chat import ChatBot

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered features using Spoon AI with Google Gemini."""
    
    def __init__(self):
        """Initialize Spoon AI client with Google Gemini."""
        # Check if API key is valid
        if settings.GOOGLE_API_KEY and not settings.GOOGLE_API_KEY.startswith("your-"):
            self.client = ChatBot(
                model_name="gemini-2.0-flash-exp",
                llm_provider="gemini"
            )
            self.enabled = True
            logger.info("AI Service initialized with Spoon AI + Google Gemini")
        else:
            self.client = None
            self.enabled = False
            logger.warning("AI Service disabled - Google API key not configured")
        
    async def generate_case(self) -> Dict[str, str]:
        """
        Generate a moral dilemma case using AI.
        
        Returns:
            Dict with 'title' and 'context' keys
            
        Raises:
            Exception: If AI generation fails
        """
        if not self.enabled:
            raise Exception("AI service not available - Google API key not configured")
        
        try:
            system_prompt = "You are a moral philosophy expert creating thought-provoking ethical dilemmas for debate."
            
            prompt = """Generate a thought-provoking moral dilemma for a debate platform.

Requirements:
- Present a clear YES/NO decision
- Controversial enough to spark debate
- Relevant to modern society
- Concise but with sufficient context
- Avoid overly political or inflammatory topics
- Frame the question for YES (moral) or NO (immoral) votes

Return JSON format:
{
  "title": "Brief question (max 150 chars)",
  "context": "Detailed scenario (200-500 words)"
}

Topics: personal ethics vs societal benefit, individual freedom vs collective good, 
technological progress vs human values, justice vs mercy, truth vs kindness.

Generate a unique, engaging moral dilemma now."""

            response = await self.client.ask(
                messages=[{"role": "user", "content": prompt}],
                system_msg=system_prompt
            )
            
            # Extract content from response
            content = response if isinstance(response, str) else str(response)
            
            # Try to parse JSON from the response
            # Spoon AI may return markdown-wrapped JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            case_data = json.loads(content)
            
            # Validate required fields
            if "title" not in case_data or "context" not in case_data:
                raise ValueError("AI response missing required fields")
            
            # Validate and truncate if needed
            if len(case_data["title"]) > 200:
                case_data["title"] = case_data["title"][:197] + "..."
            
            if len(case_data["context"]) < 100:
                raise ValueError("Context too short")
            
            if len(case_data["context"]) > 2000:
                case_data["context"] = case_data["context"][:1997] + "..."
            
            logger.info(f"✓ Generated case: {case_data['title'][:50]}...")
            return case_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            raise Exception("AI generated invalid JSON")
        except Exception as e:
            logger.error(f"Case generation failed: {str(e)}")
            raise
    
    async def generate_verdict(self, title: str, context: str) -> Dict[str, any]:
        """
        Generate an AI verdict for a moral dilemma.
        
        Args:
            title: Case title
            context: Case context
            
        Returns:
            Dict with verdict, reasoning, confidence, and verdict_hash
            
        Raises:
            Exception: If verdict generation fails
        """
        if not self.enabled:
            raise Exception("AI service not available - Google API key not configured")
        
        try:
            system_prompt = "You are an impartial moral philosophy expert providing well-reasoned ethical judgments."
            
            prompt = f"""Analyze this moral dilemma and provide a verdict:

Title: {title}

Context: {context}

As an AI moral philosophy expert:
1. Decide if morally justified (YES) or not (NO)
2. Provide clear reasoning
3. Consider multiple ethical frameworks
4. Rate confidence (0.0 to 1.0)

Return JSON:
{{
  "verdict": "YES" or "NO",
  "reasoning": "Detailed explanation (200-400 words)",
  "confidence": 0.0 to 1.0
}}

Be decisive but acknowledge complexity."""

            response = await self.client.ask(
                messages=[{"role": "user", "content": prompt}],
                system_msg=system_prompt
            )
            
            # Extract content from response
            content = response if isinstance(response, str) else str(response)
            
            # Try to parse JSON from the response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            verdict_data = json.loads(content)
            
            # Validate
            if "verdict" not in verdict_data or "reasoning" not in verdict_data:
                raise ValueError("AI response missing required fields")
            
            verdict = verdict_data["verdict"].upper().strip()
            if verdict not in ["YES", "NO"]:
                raise ValueError(f"Invalid verdict: {verdict}")
            
            confidence = verdict_data.get("confidence", 0.7)
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                confidence = 0.7
            
            # Generate verdict hash
            verdict_string = f"{verdict}|{verdict_data['reasoning']}"
            verdict_hash = hashlib.sha256(verdict_string.encode()).hexdigest()
            
            result = {
                "verdict": verdict,
                "reasoning": verdict_data["reasoning"],
                "confidence": float(confidence),
                "verdict_hash": verdict_hash
            }
            
            logger.info(f"✓ Generated verdict: {verdict} (confidence: {confidence:.2f})")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse verdict response: {str(e)}")
            raise Exception("AI generated invalid JSON")
        except Exception as e:
            logger.error(f"Verdict generation failed: {str(e)}")
            raise
    
    async def moderate_case(self, title: str, context: str) -> Tuple[bool, Optional[str]]:
        """
        Moderate user-submitted case for inappropriate content.
        
        Args:
            title: Case title
            context: Case context
            
        Returns:
            Tuple of (approved: bool, reason: Optional[str])
            
        Raises:
            Exception: If moderation check fails
        """
        # If AI is disabled, skip moderation in development mode
        if not self.enabled:
            if settings.DEBUG:
                logger.info("AI moderation bypassed (development mode)")
                return True, None
            else:
                logger.error("AI moderation required but API key not configured")
                return False, "AI moderation service unavailable"
        
        try:
            system_prompt = "You are a content moderator ensuring guidelines are followed while allowing controversial but respectful debates."
            
            prompt = f"""Review this user-submitted moral dilemma:

Title: {title}

Context: {context}

Check for:
- Hate speech, discrimination, harassment
- Graphic violence or gore
- Sexual content
- Personal attacks or doxxing
- Spam or nonsensical content
- Illegal activities
- Extreme political propaganda

The case should be:
- A genuine moral dilemma
- Respectful and thoughtful
- Appropriate for public debate

Return JSON:
{{
  "approved": true or false,
  "reason": "Brief explanation if rejected, null if approved"
}}"""

            response = await self.client.ask(
                messages=[{"role": "user", "content": prompt}],
                system_msg=system_prompt
            )
            
            # Extract content from response
            content = response if isinstance(response, str) else str(response)
            
            # Try to parse JSON from the response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            moderation_data = json.loads(content)
            
            approved = moderation_data.get("approved", False)
            reason = moderation_data.get("reason")
            
            logger.info(f"✓ Moderation: approved={approved}")
            return approved, reason
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse moderation response: {str(e)}")
            return False, "Unable to verify content appropriateness"
        except Exception as e:
            logger.error(f"Moderation failed: {str(e)}")
            return False, f"Moderation check failed: {str(e)}"
    
    async def generate_case_with_verdict(self) -> Dict[str, any]:
        """
        Generate complete case with pre-generated verdict.
        
        Used by background job to create AI-generated cases
        with hidden verdicts revealed after voting closes.
        
        Returns:
            Dict with case and verdict data
        """
        try:
            # Generate case
            case_data = await self.generate_case()
            
            # Generate verdict
            verdict_data = await self.generate_verdict(
                case_data["title"],
                case_data["context"]
            )
            
            # Set close time (24 hours from now)
            closes_at = datetime.utcnow() + timedelta(hours=24)
            
            result = {
                "title": case_data["title"],
                "context": case_data["context"],
                "verdict": verdict_data["verdict"],
                "verdict_reasoning": verdict_data["reasoning"],
                "verdict_confidence": verdict_data["confidence"],
                "verdict_hash": verdict_data["verdict_hash"],
                "closes_at": closes_at,
                "status": "active",
                "creator_id": None,
                "yes_votes": 0,
                "no_votes": 0
            }
            
            logger.info(f"✓ Complete case generated: {case_data['title'][:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Complete case generation failed: {str(e)}")
            raise


# Singleton instance
ai_service = AIService()
