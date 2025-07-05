from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz
from firebase_config import firebase_config
from google.cloud.firestore import DocumentReference
import uuid

class AppointmentManager:
    def __init__(self):
        self.db = firebase_config.get_db()
        self.appointments_collection = 'appointments'
        self.clients_collection = 'clients'
        self.trainers_collection = 'trainers'
    
    def create_client(self, name: str, phone: str, email: str = None, notes: str = None) -> str:
        """Create a new client record"""
        client_data = {
            'name': name,
            'phone': phone,
            'email': email,
            'notes': notes,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        doc_ref = self.db.collection(self.clients_collection).add(client_data)
        client_id = doc_ref[1].id
        print(f"Created client: {client_id}")
        return client_id
    
    def get_client_by_phone(self, phone: str) -> Optional[Dict]:
        """Find client by phone number"""
        clients = self.db.collection(self.clients_collection).where('phone', '==', phone).limit(1).get()
        
        if clients:
            client_doc = clients[0]
            client_data = client_doc.to_dict()
            client_data['id'] = client_doc.id
            return client_data
        return None
    
    def get_client_by_id(self, client_id: str) -> Optional[Dict]:
        """Get client by ID"""
        doc = self.db.collection(self.clients_collection).document(client_id).get()
        if doc.exists:
            client_data = doc.to_dict()
            client_data['id'] = doc.id
            return client_data
        return None
    
    def create_appointment(self, client_id: str, trainer_id: str, appointment_time: datetime, 
                          duration_minutes: int = 60, service_type: str = "Personal Training",
                          notes: str = None) -> str:
        """Create a new appointment"""
        appointment_data = {
            'client_id': client_id,
            'trainer_id': trainer_id,
            'appointment_time': appointment_time,
            'duration_minutes': duration_minutes,
            'service_type': service_type,
            'status': 'scheduled',
            'notes': notes,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'reminder_sent': False,
            'confirmation_received': False
        }
        
        doc_ref = self.db.collection(self.appointments_collection).add(appointment_data)
        appointment_id = doc_ref[1].id
        print(f"Created appointment: {appointment_id}")
        return appointment_id
    
    def get_appointments_for_client(self, client_id: str, limit: int = 10) -> List[Dict]:
        """Get appointments for a specific client"""
        appointments = (self.db.collection(self.appointments_collection)
                       .where('client_id', '==', client_id)
                       .order_by('appointment_time', direction='DESCENDING')
                       .limit(limit)
                       .get())
        
        result = []
        for doc in appointments:
            appointment_data = doc.to_dict()
            appointment_data['id'] = doc.id
            result.append(appointment_data)
        
        return result
    
    def get_upcoming_appointments(self, trainer_id: str = None, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming appointments"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=days_ahead)
        
        query = self.db.collection(self.appointments_collection)
        query = query.where('appointment_time', '>=', start_time)
        query = query.where('appointment_time', '<=', end_time)
        
        if trainer_id:
            query = query.where('trainer_id', '==', trainer_id)
        
        appointments = query.order_by('appointment_time').get()
        
        result = []
        for doc in appointments:
            appointment_data = doc.to_dict()
            appointment_data['id'] = doc.id
            result.append(appointment_data)
        
        return result
    
    def update_appointment_status(self, appointment_id: str, status: str) -> bool:
        """Update appointment status"""
        try:
            self.db.collection(self.appointments_collection).document(appointment_id).update({
                'status': status,
                'updated_at': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"Error updating appointment status: {e}")
            return False
    
    def cancel_appointment(self, appointment_id: str, reason: str = None) -> bool:
        """Cancel an appointment"""
        try:
            update_data = {
                'status': 'cancelled',
                'updated_at': datetime.utcnow()
            }
            if reason:
                update_data['cancellation_reason'] = reason
            
            self.db.collection(self.appointments_collection).document(appointment_id).update(update_data)
            return True
        except Exception as e:
            print(f"Error cancelling appointment: {e}")
            return False
    
    def reschedule_appointment(self, appointment_id: str, new_time: datetime) -> bool:
        """Reschedule an appointment"""
        try:
            self.db.collection(self.appointments_collection).document(appointment_id).update({
                'appointment_time': new_time,
                'status': 'rescheduled',
                'updated_at': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"Error rescheduling appointment: {e}")
            return False
    
    def get_available_slots(self, trainer_id: str, date: datetime, duration_minutes: int = 60) -> List[datetime]:
        """Get available time slots for a trainer on a specific date"""
        # Define business hours (9 AM to 6 PM)
        business_start = 9
        business_end = 18
        
        # Get existing appointments for the date
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        existing_appointments = (self.db.collection(self.appointments_collection)
                               .where('trainer_id', '==', trainer_id)
                               .where('appointment_time', '>=', start_of_day)
                               .where('appointment_time', '<', end_of_day)
                               .where('status', 'in', ['scheduled', 'confirmed'])
                               .get())
        
        # Create list of busy time slots
        busy_slots = []
        for doc in existing_appointments:
            appointment = doc.to_dict()
            start_time = appointment['appointment_time']
            end_time = start_time + timedelta(minutes=appointment['duration_minutes'])
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
    
    def mark_reminder_sent(self, appointment_id: str) -> bool:
        """Mark that a reminder has been sent for an appointment"""
        try:
            self.db.collection(self.appointments_collection).document(appointment_id).update({
                'reminder_sent': True,
                'reminder_sent_at': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"Error marking reminder sent: {e}")
            return False
    
    def get_appointments_needing_reminders(self, hours_ahead: int = 24) -> List[Dict]:
        """Get appointments that need reminders"""
        reminder_time = datetime.utcnow() + timedelta(hours=hours_ahead)
        
        appointments = (self.db.collection(self.appointments_collection)
                       .where('reminder_sent', '==', False)
                       .where('status', 'in', ['scheduled', 'confirmed'])
                       .where('appointment_time', '<=', reminder_time)
                       .get())
        
        result = []
        for doc in appointments:
            appointment_data = doc.to_dict()
            appointment_data['id'] = doc.id
            result.append(appointment_data)
        
        return result

# Global instance
appointment_manager = AppointmentManager() 