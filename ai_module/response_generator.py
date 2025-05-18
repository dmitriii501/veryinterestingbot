from typing import Dict, Any, Optional, List
import json
import logging
import asyncio
from datetime import datetime
from openai import OpenAI
from bot.config import app_settings

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, supabase_client):
        self.client = OpenAI(
            api_key=app_settings.AI_API_KEY.get_secret_value(),
            base_url=app_settings.AI_BASE_URL
        )
        self.supabase = supabase_client
        self.model = app_settings.AI_MODEL

    async def _fetch_employees(self, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch employees based on entities."""
        try:
            query = self.supabase.table("employees").select("*")
            
            if "department" in entities:
                query = query.ilike("department", f"%{entities['department']}%")
            if "project" in entities:
                query = query.contains("projects", [entities["project"]])
            if "date" in entities:
                # Here you would typically join with a schedule/availability table
                # For now, we'll just filter by department and project
                pass
                
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching employees: {e}")
            return []

    async def _fetch_context_data(self, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch relevant data from Supabase based on intent and entities."""
        context_data = {"found": False, "data": None, "error": None}
        
        try:
            if intent == "find_employee":
                employees = await self._fetch_employees(entities)
                context_data = {
                    "found": bool(employees),
                    "data": employees,
                    "query_params": entities
                }
            
            elif intent == "event_info":
                query = self.supabase.table("events")
                if "date" in entities:
                    query = query.eq("date", entities["date"])
                if "event_type" in entities:
                    query = query.eq("type", entities["event_type"])
                result = query.execute()
                context_data = {
                    "found": bool(result.data),
                    "data": result.data,
                    "query_params": entities
                }

            elif intent == "task_info":
                query = self.supabase.table("tasks")
                if "task_keyword" in entities:
                    query = query.ilike("description", f"%{entities['task_keyword']}%")
                result = query.execute()
                context_data = {
                    "found": bool(result.data),
                    "data": result.data,
                    "query_params": entities
                }

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
                "Если данных нет или произошла ошибка, вежливо сообщи об этом. "
                "Формат ответа должен быть естественным, как будто отвечает человек. "
                "Включи в ответ все релевантные детали из запроса: отдел, проект, дату и т.д."
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

            response = await self._call_ai_api(messages)
            if response and response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip()
            
            logger.warning("Empty response from AI model")
            return None

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None

    async def _call_ai_api(self, messages: List[Dict[str, str]]) -> Any:
        """Make the API call to the AI model."""
        try:
            return await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=0.7  # Slightly higher temperature for more natural responses
            )
        except Exception as e:
            logger.error(f"Error calling AI API: {e}")
            raise 