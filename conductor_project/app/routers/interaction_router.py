from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from app.schemas.request_schemas import ChatMessage, ChatResponse
from app.services.mcp_service import MCPService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api/v1", tags=["interaction"])

def get_mcp_service() -> MCPService:
    return MCPService()

def get_llm_service() -> LLMService:
    return LLMService()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    message: ChatMessage,
    mcp_service: MCPService = Depends(get_mcp_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Main chat endpoint for user interaction with The Sentinel via The Oracle."""
    try:
        user_input = message.content
        print(f"🎯 Chat request: '{user_input}' from user: {message.user_id}")
        
        # Check if LLM is available
        llm_available = await llm_service.is_available()
        print(f"🔮 Oracle available: {llm_available}")
        
        if llm_available:
            # Use The Oracle to interpret the request
            llm_response = await llm_service.interpret_user_request(user_input)
            
            if "error" in llm_response:
                response_text = f"Oracle unavailable: {llm_response['error']}"
                print(f"❌ Oracle error: {llm_response['error']}")
            else:
                oracle_response = llm_response.get("response", "")
                oracle_interpretation = oracle_response.lower().strip()
                print(f"🔮 Oracle interpretation: '{oracle_interpretation}'")
                
                # Check if Oracle is explicitly directing to use system commands
                # Only route to Sentinel for very specific command requests
                if ("`get_status`" in oracle_interpretation and "use the command" in oracle_interpretation) or \
                   (user_input.lower().strip() == "get_status"):
                    sentinel_response = await mcp_service.get_status()
                    if "error" in sentinel_response:
                        response_text = f"System Status Error: {sentinel_response['error']}"
                    else:
                        status = sentinel_response.get('status', 'Unknown')
                        response_text = f"System Status: {status}\n\n{oracle_response}"
                elif ("`health_check`" in oracle_interpretation and "use the command" in oracle_interpretation) or \
                     (user_input.lower().strip() == "health_check"):
                    sentinel_response = await mcp_service.health_check()
                    if "error" in sentinel_response:
                        response_text = f"System Health Error: {sentinel_response['error']}"
                    else:
                        status = sentinel_response.get('status', 'unknown')
                        response_text = f"System Health: {status}\n\n{oracle_response}"
                else:
                    # Default: Return Oracle's conversational response as primary interface
                    response_text = oracle_response
        else:
            # Fallback to simple command detection
            user_text = user_input.lower().strip()
            print(f"🔧 Using fallback mode for: '{user_text}'")
            
            if "status" in user_text:
                sentinel_response = await mcp_service.get_status()
                if "error" in sentinel_response:
                    response_text = f"Sentinel Error: {sentinel_response['error']}"
                else:
                    response_text = f"Sentinel Status: {sentinel_response.get('status', 'Unknown')}"
            elif "health" in user_text:
                sentinel_response = await mcp_service.health_check()
                if "error" in sentinel_response:
                    response_text = f"Sentinel Error: {sentinel_response['error']}"
                else:
                    status = sentinel_response.get('status', 'unknown')
                    response_text = f"Sentinel Health: {status}"
            else:
                response_text = f"Oracle offline. Available commands: 'status', 'health'. You said: {user_input}"
        
        print(f"📤 Response: '{response_text[:50]}...'")
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    
    except Exception as e:
        print(f"💥 Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/sentinel/health")
async def sentinel_health(mcp_service: MCPService = Depends(get_mcp_service)):
    """Direct endpoint to check Sentinel health."""
    return await mcp_service.health_check()

@router.get("/sentinel/status")
async def sentinel_status(mcp_service: MCPService = Depends(get_mcp_service)):
    """Direct endpoint to get Sentinel status."""
    return await mcp_service.get_status()