from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.automation.chatgpt import ChatGPTClient

router = APIRouter()

class StoryRequest(BaseModel):
    story: str

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
        expanded_story = await chatgpt_client.send_message_and_get_response(request.story)
        
        return {"expanded_story": expanded_story}
        
    except Exception as e:
        print(f"Automation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
