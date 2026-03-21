from openai import AsyncOpenAI
from fastapi import HTTPException
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize the OpenAI client for DeepSeek if API key is provided
deepseek_client = None
if settings.deepseek_api_key:
    deepseek_client = AsyncOpenAI(
        api_key=settings.deepseek_api_key,
        base_url="https://api.deepseek.com"
    )

class ModerationService:
    @staticmethod
    async def check_text_for_pii(text: str) -> None:
        """
        Analyzes the text using DeepSeek to detect Personal Identifiable Information (PII).
        Raises HTTPException 400 if PII is detected.
        """
        if not deepseek_client:
            logger.warning("DeepSeek API key not configured. Skipping text moderation.")
            return

        if not text or not text.strip():
            return

        prompt = f"""
        You are a strict text moderation system.
        Analyze the following text and determine if it contains ANY Personal Identifiable Information (PII) OR ANY indicators of a SERIOUS CRIME/malicious intent.
        
        1. PII includes:
        - Names/surnames (unless public businesses)
        - ID/social security numbers, phone numbers, exact addresses, or emails
        - Indirect references identifying a specific person
        
        2. Indicators of CRIME include ONLY serious infractions:
        - Information about empty houses or schedules when people are away (e.g., 'Casa libre los viernes', 'En el 4C libre sabados', 'Nadie de noche')
        - Voyeurism or severe privacy invasions (e.g., 'Vecina desnuda por la ventana')
        - Selling drugs or other illegal activities (e.g., 'El del 1B vende droga')

        Do NOT flag minor nuisances or neighborly complaints (e.g., playing piano at night, loud music, barking dogs) as CRIME. These are SAFE.
        Only flag CRIME if there is clear evidence of a serious or illegal act.

        Text to analyze:
        "{text}"

        Respond ONLY with a single word:
        - "PII" if the text contains PII.
        - "CRIME" if the text contains indications of a serious crime.
        - "SAFE" if the text is free of PII and serious crimes (minor complaints are SAFE).
        """

        try:
            response = await deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a strict text moderation AI."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.0
            )
            
            result = response.choices[0].message.content.strip().upper()
            
            if "PII" in result:
                logger.warning(f"PII detected in text: {text}")
                raise HTTPException(
                    status_code=400, 
                    detail="Text contains Personal Identifiable Information (PII) and cannot be saved."
                )
            elif "CRIME" in result:
                logger.warning(f"Crime indicator detected in text: {text}")
                raise HTTPException(
                    status_code=400, 
                    detail="Warning: attempted crime comment. Cannot be saved."
                )
            elif "SAFE" not in result and result not in ["NO", "NONE", ""]:
                logger.warning(f"Suspicious text detected (Fallback): {text} - Model result: {result}")
                raise HTTPException(
                    status_code=400, 
                    detail="Text violates moderation policies and cannot be saved."
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calling DeepSeek API for moderation: {e}")
            # If the API fails, we could either block or allow. Since this is strict, 
            # we might want to block or allow, but typically we allow to not break app functionality
            # when DeepSeek is down, or we block to be 100% safe. Let's log it and allow for now,
            # or raise a 500 error. The user asked to "impedir por todos los medios", so maybe 
            # failing open is bad if strictly regulated, but failing closed breaks the app if API is down.
            # We'll raise 500 if the third-party service fails, indicating temporary error.
            raise HTTPException(
                status_code=500,
                detail="Error validating text. Please try again later."
            )
