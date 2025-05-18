from typing import Dict, Any, Optional
import json
import logging
from openai import OpenAI
from bot.config import app_settings

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, supabase_client):
        self.client = OpenAI(
            api_key=app_settings.AI_API_KEY,
            base_url="https://inference.api.nscale.com/v1"
        )
        self.supabase = supabase_client
        self.model = "Qwen/Qwen3-235B-A22B"

    async def _fetch_context_data(self, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch relevant data from Supabase based on intent and entities."""
        context_data = {"found": False, "data": None}
        
        try:
            if intent == "find_employee":
                query = self.supabase.table("employees")
                if "department" in entities:
                    query = query.eq("department", entities["department"])
                if "employee_name" in entities:
                    query = query.ilike("name", f"%{entities['employee_name']}%")
                result = query.execute()
                context_data = {"found": bool(result.data), "data": result.data}

            elif intent == "event_info":
                query = self.supabase.table("events")
                if "date" in entities:
                    query = query.eq("date", entities["date"])
                if "event_type" in entities:
                    query = query.eq("type", entities["event_type"])
                result = query.execute()
                context_data = {"found": bool(result.data), "data": result.data}

            elif intent == "task_info":
                query = self.supabase.table("tasks")
                if "task_keyword" in entities:
                    query = query.ilike("description", f"%{entities['task_keyword']}%")
                result = query.execute()
                context_data = {"found": bool(result.data), "data": result.data}

        except Exception as e:
            logger.error(f"Error fetching context data: {e}")
            context_data["error"] = str(e)

        return context_data

    async def generate_response(self, nlu_result: Dict[str, Any]) -> Optional[str]:
        """Generate human-readable response based on NLU output and context data."""
        try:
            intent = nlu_result.get("intent")
            entities = nlu_result.get("entities", {})

            # Fetch relevant data from Supabase
            context_data = await self._fetch_context_data(intent, entities)

            # Prepare system prompt based on intent and context
            system_prompt = (
                "Ты — корпоративный ассистент. Твоя задача — сформировать понятный и "
                "дружелюбный ответ на основе предоставленных данных. "
                "Используй только предоставленную информацию, не выдумывай факты. "
                "Если данных нет или произошла ошибка, вежливо сообщи об этом."
            )

            # Prepare user message with context
            user_message = {
                "intent": intent,
                "entities": entities,
                "context_data": context_data
            }

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_message, ensure_ascii=False)}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip()
            
            logger.warning("Empty response from AI model")
            return None

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None 