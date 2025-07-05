from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz
from firebase_config import firebase_config
from google.cloud.firestore import FieldFilter
import uuid

class SessionManager:
    def __init__(self):
        self.db = firebase_config.get_db()
        self.sessions_collection = 'sessions'
        self.clients_collection = 'clients'
        self.users_collection = 'users'
        self.payments_collection = 'payments'
        self.training_plans_collection = 'trainingPlans'
        self.workout_logs_collection = 'workoutLogs'
    
    def get_client_by_phone(self, phone: str) -> Optional[Dict]:
        """Find client by phone number"""
        try:
            clients = self.db.collection(self.clients_collection).where('phone', '==', phone).limit(1).get()
            
            if clients:
                client_doc = clients[0]
                client_data = client_doc.to_dict()
                client_data['id'] = client_doc.id
                return client_data
            return None
        except Exception as e:
            print(f"Error finding client by phone: {e}")
            return None
    
    def get_client_by_id(self, client_id: str) -> Optional[Dict]:
        """Get client by ID"""
        try:
            doc = self.db.collection(self.clients_collection).document(client_id).get()
            if doc.exists:
                client_data = doc.to_dict()
                client_data['id'] = doc.id
                return client_data
            return None
        except Exception as e:
            print(f"Error getting client by ID: {e}")
            return None
    
    def create_client(self, name: str, phone: str, email: str = None, goals: str = None, 
                     trainer_id: str = None, package_size: int = 0) -> str:
        """Create a new client record"""
        try:
            client_data = {
                'name': name,
                'phone': phone,
                'email': email,
                'goals': goals or "",
                'injuries': "",
                'startDate': datetime.utcnow(),
                'notes': "",
                'trainerId': trainer_id or "",
                'createdAt': datetime.utcnow(),
                'lastSessionDate': None,
                'sessionsRemaining': 0,
                'packageSize': package_size,
                'updatedAt': datetime.utcnow()
            }
            
            doc_ref = self.db.collection(self.clients_collection).add(client_data)
            client_id = doc_ref[1].id
            print(f"Created client: {client_id}")
            return client_id
        except Exception as e:
            print(f"Error creating client: {e}")
            return None
    
    def create_session(self, client_id: str, client_name: str, trainer_id: str, 
                      session_time: datetime, location: str = "Gym", 
                      duration: int = 60, notes: str = "") -> str:
        """Create a new training session"""
        try:
            session_data = {
                'clientId': client_id,
                'clientName': client_name,
                'dateTime': session_time,
                'location': location,
                'status': 'scheduled',
                'notes': notes,
                'duration': duration,
                'autoReminderSent': False,
                'trainerId': trainer_id,
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow()
            }
            
            doc_ref = self.db.collection(self.sessions_collection).add(session_data)
            session_id = doc_ref[1].id
            print(f"Created session: {session_id}")
            return session_id
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
    
    def get_sessions_for_client(self, client_id: str, limit: int = 10) -> List[Dict]:
        """Get sessions for a specific client"""
        try:
            sessions = (self.db.collection(self.sessions_collection)
                           .where('clientId', '==', client_id)
                           .order_by('dateTime', direction='DESCENDING')
                           .limit(limit)
                           .get())
            
            result = []
            for doc in sessions:
                session_data = doc.to_dict()
                session_data['id'] = doc.id
                result.append(session_data)
            
            return result
        except Exception as e:
            print(f"Error getting sessions for client: {e}")
            return []
    
    def get_upcoming_sessions(self, trainer_id: str = None, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming sessions"""
        try:
            start_time = datetime.utcnow()
            end_time = start_time + timedelta(days=days_ahead)
            
            query = self.db.collection(self.sessions_collection)
            query = query.where('dateTime', '>=', start_time)
            query = query.where('dateTime', '<=', end_time)
            
            if trainer_id:
                query = query.where('trainerId', '==', trainer_id)
            
            sessions = query.order_by('dateTime').get()
            
            result = []
            for doc in sessions:
                session_data = doc.to_dict()
                session_data['id'] = doc.id
                result.append(session_data)
            
            return result
        except Exception as e:
            print(f"Error getting upcoming sessions: {e}")
            return []
    
    def update_session_status(self, session_id: str, status: str) -> bool:
        """Update session status"""
        try:
            self.db.collection(self.sessions_collection).document(session_id).update({
                'status': status,
                'updatedAt': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"Error updating session status: {e}")
            return False
    
    def cancel_session(self, session_id: str, reason: str = None) -> bool:
        """Cancel a session"""
        try:
            update_data = {
                'status': 'cancelled',
                'updatedAt': datetime.utcnow()
            }
            if reason:
                update_data['cancellationReason'] = reason
            
            self.db.collection(self.sessions_collection).document(session_id).update(update_data)
            return True
        except Exception as e:
            print(f"Error cancelling session: {e}")
            return False
    
    def reschedule_session(self, session_id: str, new_time: datetime) -> bool:
        """Reschedule a session"""
        try:
            self.db.collection(self.sessions_collection).document(session_id).update({
                'dateTime': new_time,
                'status': 'scheduled',
                'updatedAt': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"Error rescheduling session: {e}")
            return False
    
    def get_available_slots(self, trainer_id: str, date: datetime, duration_minutes: int = 60) -> List[datetime]:
        """Get available time slots for a trainer on a specific date"""
        try:
            # Define business hours (9 AM to 6 PM)
            business_start = 9
            business_end = 18
            
            # Get existing sessions for the date
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            existing_sessions = (self.db.collection(self.sessions_collection)
                                   .where('trainerId', '==', trainer_id)
                                   .where('dateTime', '>=', start_of_day)
                                   .where('dateTime', '<', end_of_day)
                                   .where('status', 'in', ['scheduled'])
                                   .get())
            
            # Create list of busy time slots
            busy_slots = []
            for doc in existing_sessions:
                session = doc.to_dict()
                start_time = session['dateTime']
                duration = session.get('duration', 60)
                end_time = start_time + timedelta(minutes=duration)
                busy_slots.append((start_time, end_time))
            
            # Generate available slots
            available_slots = []
            current_time = start_of_day.replace(hour=business_start)
            end_time = start_of_day.replace(hour=business_end)
            
            while current_time + timedelta(minutes=duration_minutes) <= end_time:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Check if this slot conflicts with any busy slot
                is_available = True
                for busy_start, busy_end in busy_slots:
                    if (current_time < busy_end and slot_end > busy_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append(current_time)
                
                current_time += timedelta(minutes=30)  # 30-minute intervals
            
            return available_slots
        except Exception as e:
            print(f"Error getting available slots: {e}")
            return []
    
    def mark_reminder_sent(self, session_id: str, method: str = "phone") -> bool:
        """Mark that a reminder has been sent for a session"""
        try:
            self.db.collection(self.sessions_collection).document(session_id).update({
                'autoReminderSent': True,
                'lastReminderMethod': method,
                'reminderSentAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"Error marking reminder sent: {e}")
            return False
    
    def get_sessions_needing_reminders(self, hours_ahead: int = 24) -> List[Dict]:
        """Get sessions that need reminders"""
        try:
            reminder_time = datetime.utcnow() + timedelta(hours=hours_ahead)
            
            sessions = (self.db.collection(self.sessions_collection)
                           .where('autoReminderSent', '==', False)
                           .where('status', '==', 'scheduled')
                           .where('dateTime', '<=', reminder_time)
                           .get())
            
            result = []
            for doc in sessions:
                session_data = doc.to_dict()
                session_data['id'] = doc.id
                result.append(session_data)
            
            return result
        except Exception as e:
            print(f"Error getting sessions needing reminders: {e}")
            return []
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        try:
            doc = self.db.collection(self.sessions_collection).document(session_id).get()
            if doc.exists:
                session_data = doc.to_dict()
                session_data['id'] = doc.id
                return session_data
            return None
        except Exception as e:
            print(f"Error getting session by ID: {e}")
            return None
    
    def get_trainer_by_id(self, trainer_id: str) -> Optional[Dict]:
        """Get trainer by ID"""
        try:
            doc = self.db.collection(self.users_collection).document(trainer_id).get()
            if doc.exists:
                trainer_data = doc.to_dict()
                trainer_data['id'] = doc.id
                return trainer_data
            return None
        except Exception as e:
            print(f"Error getting trainer by ID: {e}")
            return None
    
    def get_client_sessions_remaining(self, client_id: str) -> int:
        """Get remaining sessions for a client"""
        try:
            client = self.get_client_by_id(client_id)
            if client:
                return client.get('sessionsRemaining', 0)
            return 0
        except Exception as e:
            print(f"Error getting client sessions remaining: {e}")
            return 0
    
    def update_client_sessions_remaining(self, client_id: str, sessions_remaining: int) -> bool:
        """Update remaining sessions for a client"""
        try:
            self.db.collection(self.clients_collection).document(client_id).update({
                'sessionsRemaining': sessions_remaining,
                'updatedAt': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"Error updating client sessions remaining: {e}")
            return False

# Global instance
session_manager = SessionManager() 