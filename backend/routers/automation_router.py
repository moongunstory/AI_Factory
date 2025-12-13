from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.automation.chatgpt import ChatGPTClient

router = APIRouter()

class StoryRequest(BaseModel):
    story: str

class WorkflowResponse(BaseModel):
    expanded_story: str
    storyboard: str
    prompts: str

# Global instance to keep browser open (optional, but good for performance)
# For now, we instantiate per request or use a singleton pattern if we want to keep the window open.
# To allow the "Persistent" feel, let's try to keep it alive or re-attach.
chatgpt_client = ChatGPTClient()

@router.post("/expand-story")
async def expand_story(request: StoryRequest):
    """
    Expands the given story prompt using the local ChatGPT automation.
    Requires the user to be logged in to the opened browser window.
    """
    try:
        # Start the browser if not running
        await chatgpt_client.start_browser()

        # Send prompt
        expanded_story = await chatgpt_client.send_message_and_get_response(
            request.story,
            ChatGPTClient.GPT_URLS["fable_forge"]
        )

        return {"expanded_story": expanded_story}

    except Exception as e:
        print(f"Automation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-video-workflow", response_model=WorkflowResponse)
async def generate_video_workflow(request: StoryRequest):
    """
    전체 비디오 생성 워크플로우를 실행합니다:
    1. Fable Forge: 이야기 확장
    2. Storyboard GPT: 스토리보드 작성
    3. Storyboard Maker: 프롬프트 생성

    브라우저가 열리고 ChatGPT에 로그인되어 있어야 합니다.
    세션은 자동으로 유지되므로 한 번만 로그인하면 됩니다.
    """
    try:
        # 3단계 워크플로우 실행
        results = await chatgpt_client.run_video_generation_workflow(request.story)

        return WorkflowResponse(
            expanded_story=results["expanded_story"],
            storyboard=results["storyboard"],
            prompts=results["prompts"]
        )

    except Exception as e:
        print(f"Workflow Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
