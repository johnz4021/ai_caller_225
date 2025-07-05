import logging
import os
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn
from contextlib import asynccontextmanager

from config import BASE_URL

from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.telephony.server.base import TelephonyServer
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import ElevenLabsSynthesizerConfig
from vocode.streaming.models.transcriber import DeepgramTranscriberConfig

# Import both if using ngrok
# from pyngrok import ngrok
# import sys
from memory_config import config_manager
from vocode.streaming.models.synthesizer import StreamElementsSynthesizerConfig # ,ElevenLabsSynthesizerConfig

# Imports our custom actions
from speller_agent import SpellerAgentFactory

# Import appointment scheduling components
try:
    from appointment_agent import AppointmentAgentFactory
    APPOINTMENT_SCHEDULING_ENABLED = True
except ImportError:
    print("Warning: Appointment scheduling not available. Install firebase-admin to enable.")
    APPOINTMENT_SCHEDULING_ENABLED = False

# Imports additional events like transcripts
from events_manager import EventsManager

# if running from python, this will load the local .env
# docker-compose will load the .env file by itself
from dotenv import load_dotenv

load_dotenv()

# Try to import session-related modules
try:
    from utils.session_utils import session_manager
    from session_agent import SessionAgentFactory
    from outbound_session_calls import session_outbound_caller
    SESSION_SYSTEM_AVAILABLE = True
    print("✅ Session scheduling system loaded successfully")
except ImportError as e:
    print(f"⚠️  Session scheduling system not available: {e}")
    print("   Using basic agent configuration")
    SESSION_SYSTEM_AVAILABLE = False

# Check if we should use session agent
USE_SESSION_AGENT = os.getenv("USE_SESSION_AGENT", "true").lower() == "true"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Personal Training AI Call System...")
    
    # Test Firebase connection if session system is available
    if SESSION_SYSTEM_AVAILABLE:
        try:
            # Test Firebase connection
            trainer = session_manager.get_trainer_by_id("8QYQXt91Kzf4j4w0i2kogb4zEyN2")
            if trainer:
                print(f"✅ Firebase connected - Trainer: {trainer.get('name', 'Unknown')}")
            else:
                print("⚠️  Firebase connected but trainer not found")
        except Exception as e:
            print(f"❌ Firebase connection error: {e}")
    
    print("✅ System ready for calls!")
    yield
    
    # Shutdown
    print("🛑 Shutting down...")

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan, title="Personal Training AI Call System")

# Initialize logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# We store the state of the call in memory
# You can customize the config within the memory_config.py
CONFIG_MANAGER = config_manager  #RedisConfigManager()

# Activate this if you want to support NGROK
# if not BASE_URL:
#     ngrok_auth = os.environ.get("NGROK_AUTH_TOKEN")
#     if ngrok_auth is not None:
#         ngrok.set_auth_token(ngrok_auth)
#     port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 3000
# 
#     # Open a ngrok tunnel to the dev server
#     BASE_URL = ngrok.connect(port).public_url.replace("https://", "")
#     logger.info('ngrok tunnel "{}" -> "http://127.0.0.1:{}"'.format(BASE_URL, port))
# 

# Only continue of the base URL was set within the environment variable. 
if not BASE_URL:
    raise ValueError("BASE_URL must be set in environment if not using pyngrok")

# Now we need a Twilio account and number from which to make our call.
# You can make an account here: https://www.twilio.com/docs/iam/access-tokens#step-2-api-key
# Ensure your account is NOT in trial as otherwise it won't work
TWILIO_CONFIG = TwilioConfig(
  account_sid=os.environ.get("TWILIO_ACCOUNT_SID"),
  auth_token=os.environ.get("TWILIO_AUTH_TOKEN"),
)

# Create agent configuration
def create_agent_config():
    """Create agent configuration based on available systems"""
    
    if SESSION_SYSTEM_AVAILABLE and USE_SESSION_AGENT:
        # Use session scheduling agent
        initial_message = "Hello! I'm your personal training assistant. I can help you schedule, reschedule, or cancel your training sessions. I can also check your remaining sessions and answer questions about your training. How can I help you today?"
        
        prompt = """
You are a professional personal training assistant for a fitness business. You help clients with their training sessions and provide excellent customer service.

CORE CAPABILITIES:
- Schedule new training sessions
- Reschedule existing sessions  
- Cancel sessions
- Check session availability
- Verify remaining sessions in client packages
- Answer questions about training programs
- Provide session confirmations and reminders

IMPORTANT GUIDELINES:
1. Always be professional, friendly, and helpful
2. Collect essential information: client name, phone number, preferred date/time
3. Confirm all session details before booking
4. Check if clients have remaining sessions before scheduling
5. Offer alternative times if requested slots are unavailable
6. Keep conversations focused and efficient
7. Provide clear confirmations for all actions

REQUIRED INFORMATION FOR SCHEDULING:
- Client name
- Phone number  
- Preferred date and time
- Location (default: Gym)

BUSINESS HOURS: 9:00 AM - 6:00 PM, Monday through Sunday
SESSION DURATION: 60 minutes (default)
LOCATION: Gym (default)

Always end calls with a clear summary of what was accomplished and next steps.
"""
    else:
        # Use basic agent configuration
        initial_message = "Hello! Thanks for calling our personal training service. How can I help you today?"
        
        prompt = """
You are a helpful customer service representative for a personal training business. 
Be professional, friendly, and helpful. Answer questions about training services, 
scheduling, and general inquiries. If you cannot help with something specific, 
politely direct them to contact the business directly.
"""
    
    return ChatGPTAgentConfig(
        initial_message=BaseMessage(text=initial_message),
        prompt_preamble=prompt,
        generate_responses=True,
    )

# Create agent factory
def create_agent_factory():
    """Create appropriate agent factory"""
    if SESSION_SYSTEM_AVAILABLE and USE_SESSION_AGENT:
        return SessionAgentFactory()
    else:
        # Return basic agent factory
        from vocode.streaming.agent.factory import AgentFactory
        return AgentFactory()

# Configure telephony server
agent_config = create_agent_config()
agent_factory = create_agent_factory()

# Create transcriber and synthesizer configs
transcriber_config = DeepgramTranscriberConfig(
    model="nova-2",
    language="en-US",
)

synthesizer_config = ElevenLabsSynthesizerConfig(
    voice_id=os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
    stability=0.1,
    similarity_boost=0.75,
)

# Create telephony server
telephony_server = TelephonyServer(
    base_url=os.getenv("BASE_URL"),
    config_manager=None,  # We'll handle config manually
    inbound_call_configs=[],
    agent_factory=agent_factory,
    transcriber_config=transcriber_config,
    synthesizer_config=synthesizer_config,
)

# Mount telephony server
app.mount("/", telephony_server.get_router())

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "session_system": SESSION_SYSTEM_AVAILABLE,
        "use_session_agent": USE_SESSION_AGENT,
        "firebase_connected": False
    }
    
    # Test Firebase connection if available
    if SESSION_SYSTEM_AVAILABLE:
        try:
            trainer = session_manager.get_trainer_by_id("8QYQXt91Kzf4j4w0i2kogb4zEyN2")
            status["firebase_connected"] = trainer is not None
        except:
            status["firebase_connected"] = False
    
    return status

# Session management endpoints (if available)
if SESSION_SYSTEM_AVAILABLE:
    
    @app.get("/sessions/upcoming")
    async def get_upcoming_sessions():
        """Get upcoming sessions"""
        try:
            sessions = session_manager.get_upcoming_sessions(
                trainer_id="8QYQXt91Kzf4j4w0i2kogb4zEyN2",
                days_ahead=7
            )
            return {"sessions": sessions}
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/sessions/reminders")
    async def get_sessions_needing_reminders():
        """Get sessions that need reminders"""
        try:
            sessions = session_manager.get_sessions_needing_reminders(hours_ahead=24)
            return {"sessions": sessions}
        except Exception as e:
            return {"error": str(e)}
    
    @app.post("/sessions/send-reminders")
    async def send_session_reminders():
        """Send reminder calls for upcoming sessions"""
        try:
            stats = await session_outbound_caller.process_reminder_queue(hours_ahead=24)
            return {"status": "completed", "stats": stats}
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/clients/{client_id}/sessions")
    async def get_client_sessions(client_id: str):
        """Get sessions for a specific client"""
        try:
            sessions = session_manager.get_sessions_for_client(client_id)
            return {"sessions": sessions}
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/clients/{client_id}/remaining-sessions")
    async def get_client_remaining_sessions(client_id: str):
        """Get remaining sessions for a client"""
        try:
            remaining = session_manager.get_client_sessions_remaining(client_id)
            return {"remaining_sessions": remaining}
        except Exception as e:
            return {"error": str(e)}

# Manual testing endpoints
@app.post("/test/outbound-call")
async def test_outbound_call(phone_number: str, call_type: str = "scheduling"):
    """Test outbound calling functionality"""
    if not SESSION_SYSTEM_AVAILABLE:
        return {"error": "Session system not available"}
    
    try:
        if call_type == "scheduling":
            success = await session_outbound_caller.make_scheduling_call(phone_number)
        elif call_type == "follow_up":
            # Find client by phone for follow-up
            client = session_manager.get_client_by_phone(phone_number)
            if client:
                success = await session_outbound_caller.make_follow_up_call(client['id'])
            else:
                return {"error": "Client not found"}
        else:
            return {"error": "Invalid call type"}
        
        return {"success": success, "call_type": call_type, "phone": phone_number}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Run the server
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting server on {host}:{port}")
    print(f"📱 Session system: {'✅ Enabled' if SESSION_SYSTEM_AVAILABLE else '❌ Disabled'}")
    print(f"🤖 Agent type: {'Session Agent' if (SESSION_SYSTEM_AVAILABLE and USE_SESSION_AGENT) else 'Basic Agent'}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
