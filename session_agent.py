from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
from dateutil import parser
import pytz

from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.agent.base_agent import BaseAgent
from vocode.streaming.agent.factory import AgentFactory

from utils.session_utils import session_manager

class SessionSchedulingAgent(BaseAgent):
    """
    Custom agent for handling training session scheduling conversations
    """
    
    def __init__(self, agent_config: ChatGPTAgentConfig):
        super().__init__(agent_config)
        self.session_manager = session_manager
        self.conversation_context = {}
        
    def get_session_instructions(self) -> str:
        """Get specialized instructions for session scheduling"""
        return """
You are a professional training session scheduling assistant for a personal training business. Your primary role is to help clients schedule, reschedule, or cancel their training sessions.

CAPABILITIES:
- Schedule new training sessions
- Check session availability
- Reschedule existing sessions
- Cancel sessions
- Provide session confirmations
- Send session reminders
- Check remaining sessions in client packages

CONVERSATION GUIDELINES:
1. Be professional, friendly, and efficient
2. Always confirm session details before booking
3. Ask for essential information: name, phone number, preferred date/time
4. Offer alternative times if requested slot is unavailable
5. Confirm all changes and provide session details
6. Keep responses concise and action-oriented
7. Check if client has remaining sessions in their package

REQUIRED INFORMATION FOR BOOKING:
- Client name
- Phone number
- Preferred date and time
- Training location (default: Gym)

AVAILABLE ACTIONS:
- "SCHEDULE_SESSION" - Create new training session
- "RESCHEDULE_SESSION" - Change existing session
- "CANCEL_SESSION" - Cancel session
- "CHECK_AVAILABILITY" - Check available time slots
- "CONFIRM_SESSION" - Confirm session details
- "CHECK_REMAINING_SESSIONS" - Check client's remaining sessions

Always end conversations with a clear summary of what was accomplished.
"""
    
    def extract_session_intent(self, message: str) -> Dict:
        """Extract session-related intent from user message"""
        message_lower = message.lower()
        
        # Intent detection
        if any(word in message_lower for word in ['schedule', 'book', 'session', 'training']):
            intent = 'schedule'
        elif any(word in message_lower for word in ['reschedule', 'change', 'move']):
            intent = 'reschedule'
        elif any(word in message_lower for word in ['cancel', 'remove']):
            intent = 'cancel'
        elif any(word in message_lower for word in ['available', 'availability', 'free']):
            intent = 'check_availability'
        elif any(word in message_lower for word in ['remaining', 'sessions left', 'how many']):
            intent = 'check_remaining'
        else:
            intent = 'general'
        
        # Extract potential dates and times
        date_patterns = [
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(today|tomorrow|next week)\b'
        ]
        
        time_patterns = [
            r'\b(\d{1,2}:\d{2}\s*(?:am|pm))\b',
            r'\b(\d{1,2}\s*(?:am|pm))\b',
            r'\b(morning|afternoon|evening)\b'
        ]
        
        extracted_dates = []
        extracted_times = []
        
        for pattern in date_patterns:
            matches = re.findall(pattern, message_lower)
            extracted_dates.extend(matches)
        
        for pattern in time_patterns:
            matches = re.findall(pattern, message_lower)
            extracted_times.extend(matches)
        
        # Extract phone number
        phone_pattern = r'\b(\d{3}[-.]?\d{3}[-.]?\d{4})\b'
        phone_matches = re.findall(phone_pattern, message)
        
        # Extract name (simple heuristic)
        name_patterns = [
            r'my name is ([a-zA-Z\s]+)',
            r'i\'m ([a-zA-Z\s]+)',
            r'this is ([a-zA-Z\s]+)'
        ]
        
        extracted_names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, message_lower)
            extracted_names.extend(matches)
        
        return {
            'intent': intent,
            'dates': extracted_dates,
            'times': extracted_times,
            'phone': phone_matches[0] if phone_matches else None,
            'name': extracted_names[0].strip() if extracted_names else None
        }
    
    def format_available_slots(self, slots: List[datetime]) -> str:
        """Format available time slots for display"""
        if not slots:
            return "No available slots found for the requested date."
        
        formatted_slots = []
        for slot in slots[:5]:  # Show first 5 slots
            formatted_time = slot.strftime("%I:%M %p")
            formatted_slots.append(formatted_time)
        
        return f"Available times: {', '.join(formatted_slots)}"
    
    def process_scheduling_request(self, extracted_info: Dict, conversation_id: str) -> str:
        """Process session scheduling request"""
        intent = extracted_info['intent']
        
        if intent == 'schedule':
            return self.handle_schedule_request(extracted_info, conversation_id)
        elif intent == 'reschedule':
            return self.handle_reschedule_request(extracted_info, conversation_id)
        elif intent == 'cancel':
            return self.handle_cancel_request(extracted_info, conversation_id)
        elif intent == 'check_availability':
            return self.handle_availability_request(extracted_info, conversation_id)
        elif intent == 'check_remaining':
            return self.handle_remaining_sessions_request(extracted_info, conversation_id)
        else:
            return "I can help you schedule, reschedule, or cancel training sessions. I can also check your remaining sessions. What would you like to do?"
    
    def handle_schedule_request(self, extracted_info: Dict, conversation_id: str) -> str:
        """Handle session scheduling request"""
        # Store context for multi-turn conversation
        if conversation_id not in self.conversation_context:
            self.conversation_context[conversation_id] = {}
        
        context = self.conversation_context[conversation_id]
        
        # Update context with extracted information
        if extracted_info['name']:
            context['name'] = extracted_info['name']
        if extracted_info['phone']:
            context['phone'] = extracted_info['phone']
        if extracted_info['dates']:
            context['date'] = extracted_info['dates'][0]
        if extracted_info['times']:
            context['time'] = extracted_info['times'][0]
        
        # Check if we have all required information
        required_fields = ['name', 'phone', 'date', 'time']
        missing_fields = [field for field in required_fields if field not in context]
        
        if missing_fields:
            if 'name' in missing_fields:
                return "I'd be happy to schedule a training session for you. Could you please tell me your name?"
            elif 'phone' in missing_fields:
                return "Great! Could you please provide your phone number for the session?"
            elif 'date' in missing_fields:
                return "What date would you prefer for your training session?"
            elif 'time' in missing_fields:
                return "What time would work best for you?"
        
        # All information collected, attempt to schedule
        try:
            # Parse date and time
            date_str = context['date']
            time_str = context['time']
            
            # Simple date parsing (you may want to enhance this)
            if date_str.lower() == 'today':
                session_date = datetime.now().date()
            elif date_str.lower() == 'tomorrow':
                session_date = (datetime.now() + timedelta(days=1)).date()
            else:
                # Try to parse the date
                session_date = parser.parse(date_str).date()
            
            # Parse time
            session_time = parser.parse(time_str).time()
            
            # Combine date and time
            session_datetime = datetime.combine(session_date, session_time)
            
            # Check if client exists
            client = self.session_manager.get_client_by_phone(context['phone'])
            if not client:
                # Create new client
                client_id = self.session_manager.create_client(
                    name=context['name'],
                    phone=context['phone'],
                    trainer_id="8QYQXt91Kzf4j4w0i2kogb4zEyN2"  # Default trainer ID from your data
                )
                if not client_id:
                    return "I'm sorry, there was an issue creating your client profile. Please try again."
            else:
                client_id = client['id']
            
            # Check remaining sessions
            remaining_sessions = self.session_manager.get_client_sessions_remaining(client_id)
            if remaining_sessions <= 0:
                return f"I see you don't have any remaining sessions in your package. Please contact your trainer to purchase more sessions before scheduling."
            
            # Create session
            session_id = self.session_manager.create_session(
                client_id=client_id,
                client_name=context['name'],
                trainer_id="8QYQXt91Kzf4j4w0i2kogb4zEyN2",  # Default trainer ID
                session_time=session_datetime,
                location="Gym",
                duration=60
            )
            
            if session_id:
                # Update remaining sessions
                self.session_manager.update_client_sessions_remaining(client_id, remaining_sessions - 1)
                
                # Clear context
                self.conversation_context[conversation_id] = {}
                
                return f"Perfect! I've scheduled your training session for {session_datetime.strftime('%A, %B %d at %I:%M %p')} at the Gym. You have {remaining_sessions - 1} sessions remaining in your package. You'll receive a confirmation shortly."
            else:
                return "I'm sorry, there was an issue scheduling your session. Please try again."
            
        except Exception as e:
            return f"I'm sorry, there was an issue scheduling your session. Could you please provide the date and time in a different format? For example: 'Monday at 2 PM' or '12/15/2023 at 3:30 PM'"
    
    def handle_reschedule_request(self, extracted_info: Dict, conversation_id: str) -> str:
        """Handle session rescheduling request"""
        return "I can help you reschedule your training session. Could you please provide your phone number and the new date and time you'd prefer?"
    
    def handle_cancel_request(self, extracted_info: Dict, conversation_id: str) -> str:
        """Handle session cancellation request"""
        return "I can help you cancel your training session. Could you please provide your phone number so I can find your upcoming sessions?"
    
    def handle_availability_request(self, extracted_info: Dict, conversation_id: str) -> str:
        """Handle availability check request"""
        if extracted_info['dates']:
            try:
                date_str = extracted_info['dates'][0]
                if date_str.lower() == 'today':
                    check_date = datetime.now()
                elif date_str.lower() == 'tomorrow':
                    check_date = datetime.now() + timedelta(days=1)
                else:
                    check_date = parser.parse(date_str)
                
                available_slots = self.session_manager.get_available_slots(
                    trainer_id="8QYQXt91Kzf4j4w0i2kogb4zEyN2",  # Default trainer ID
                    date=check_date
                )
                
                return self.format_available_slots(available_slots)
            except:
                return "I'm sorry, I couldn't understand that date. Could you please specify the date you'd like to check availability for?"
        else:
            return "What date would you like to check availability for?"
    
    def handle_remaining_sessions_request(self, extracted_info: Dict, conversation_id: str) -> str:
        """Handle remaining sessions check request"""
        if extracted_info['phone']:
            client = self.session_manager.get_client_by_phone(extracted_info['phone'])
            if client:
                remaining = self.session_manager.get_client_sessions_remaining(client['id'])
                return f"You have {remaining} training sessions remaining in your package."
            else:
                return "I couldn't find your client profile. Could you please verify your phone number?"
        else:
            return "Could you please provide your phone number so I can check your remaining sessions?"

class SessionAgentFactory(AgentFactory):
    """Factory for creating session scheduling agents"""
    
    def create_agent(self, agent_config: ChatGPTAgentConfig) -> BaseAgent:
        # Override the prompt for session scheduling
        session_instructions = SessionSchedulingAgent(agent_config).get_session_instructions()
        
        # Create a new config with session-specific instructions
        session_config = ChatGPTAgentConfig(
            initial_message=BaseMessage(text="Hello! I'm here to help you schedule your personal training session. How can I assist you today?"),
            prompt_preamble=session_instructions,
            generate_responses=True,
        )
        
        return SessionSchedulingAgent(session_config) 