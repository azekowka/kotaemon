from typing import List, AsyncGenerator, Dict, Any
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from ktem.components import reasonings # Import reasonings
from ktem.index.file.index import FileIndex
from ktem.reasoning.prompt_optimization.suggest_followup_chat import SuggestFollowupQuesPipeline
from ktem.utils.lang import SUPPORTED_LANGUAGE_MAP

from ..dependencies import get_application, get_index_manager
from kotaemon.base import Document

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatMessage(BaseModel):
    message: str
    history: List[List[str]] = []
    conversation_id: str = ""
    reasoning_type: str = "simple"
    llm_type: str = ""
    use_mind_map: bool = False
    use_citation: str = "off"
    language: str = "English"
    user_id: str = "default"
    selected_file_ids: List[str] = []

async def stream_chat_response(generator: AsyncGenerator) -> AsyncGenerator[str, None]:
    async for item in generator:
        if isinstance(item, Document):
            yield json.dumps(item.model_dump()) + "\n"
        else:
            # Handle other types if necessary, or just stringify
            yield str(item) + "\n"

@router.post("/message")
async def post_message(
    chat_message: ChatMessage,
    app_instance: get_application = Depends(),
    index_manager: get_index_manager = Depends(),
) -> StreamingResponse:
    """Handle incoming chat messages and generate a response."""
    try:
        # 1. Retrieve documents based on selected_file_ids
        retrievers = []
        if chat_message.selected_file_ids:
            file_index: FileIndex = None
            for index in index_manager.indices:
                if isinstance(index, FileIndex):
                    file_index = index
                    break
            
            if file_index:
                retrievers = file_index.get_retriever_pipelines(
                    app_instance.default_settings.flatten(),
                    chat_message.user_id,
                    chat_message.selected_file_ids
                )

        # 2. Get the reasoning class
        reasoning_cls = reasonings.get(chat_message.reasoning_type)
        if not reasoning_cls:
            raise HTTPException(status_code=400, detail=f"Unknown reasoning type: {chat_message.reasoning_type}")

        # Prepare settings for the pipeline
        settings = app_instance.default_settings.flatten()
        # Override settings with chat message parameters if provided
        if chat_message.llm_type:
            settings[f"reasoning.options.{reasoning_cls.get_info()['id']}.llm"] = chat_message.llm_type
        settings[f"reasoning.options.{reasoning_cls.get_info()['id']}.create_mindmap"] = chat_message.use_mind_map
        settings[f"reasoning.options.{reasoning_cls.get_info()['id']}.highlight_citation"] = chat_message.use_citation
        settings["reasoning.lang"] = chat_message.language

        # 3. Create a reasoning pipeline instance
        # We need a dummy state object, as the original Gradio app uses a state object
        dummy_state = {"app": {"regen": False}}
        pipeline = reasoning_cls.get_pipeline(settings, dummy_state, retrievers)

        # 4. Stream response from the LLM
        response_generator = pipeline.stream(
            message=chat_message.message,
            conv_id=chat_message.conversation_id,
            history=chat_message.history,
            user_id=chat_message.user_id,
        )

        return StreamingResponse(stream_chat_response(response_generator), media_type="application/x-ndjson")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/suggestions")
async def get_chat_suggestions(
    app_instance: get_application = Depends(),
    current_history: List[List[str]] = [], # Optional: to generate context-aware suggestions
    language: str = "English",
) -> Dict[str, Any]:
    """Generate chat suggestions."""
    try:
        suggest_pipeline = SuggestFollowupQuesPipeline()
        target_language = SUPPORTED_LANGUAGE_MAP.get(language, "English")
        suggest_pipeline.lang = target_language

        suggested_questions = []
        if current_history:
            suggested_resp = suggest_pipeline(current_history).text
            if ques_res := json.dumps(suggested_resp):
                try:
                    parsed_questions = json.loads(ques_res)
                    if isinstance(parsed_questions, list):
                        suggested_questions = [x for x in parsed_questions]
                    else:
                        suggested_questions = [parsed_questions]
                except json.JSONDecodeError:
                    suggested_questions = [suggested_resp]
        
        # Combine with default samples if needed, or just use generated ones
        if not suggested_questions:
            suggested_questions = [item[0] for item in app_instance.chat_suggestion.chat_samples]

        return {"suggestions": suggested_questions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")
