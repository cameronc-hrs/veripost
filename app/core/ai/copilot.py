"""AI Copilot for post processor analysis and guidance.

Uses Claude as the AI backbone, positioning AI as an enabler rather than the product.
The copilot assists CAM engineers with understanding, modifying, and troubleshooting
post processors without replacing their expertise.
"""

from app.config import get_settings
from app.core.ai.prompts import SYSTEM_PROMPT


class Copilot:
    """AI-powered assistant for post processor tasks."""

    async def ask(
        self,
        context: str,
        question: str,
        platform: str = "camworks",
    ) -> str:
        """Ask the copilot a question about a post processor.

        Args:
            context: The raw post processor content or parsed summary.
            question: The engineer's question.
            platform: The CAM platform (camworks, delmia, mastercam).

        Returns:
            The AI-generated response.
        """
        settings = get_settings()

        if not settings.anthropic_api_key:
            return "[Copilot unavailable — ANTHROPIC_API_KEY not configured]"

        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

            message = await client.messages.create(
                model=settings.ai_model,
                max_tokens=2048,
                system=SYSTEM_PROMPT.format(platform=platform),
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Here is a {platform} post processor file:\n\n"
                            f"```\n{context[:8000]}\n```\n\n"
                            f"Question: {question}"
                        ),
                    }
                ],
            )

            return message.content[0].text

        except Exception as e:
            return f"[Copilot error: {e}]"
