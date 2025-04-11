from multiprocessing import shared_memory, Lock
from queue import Queue
from threading import Thread, Event
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import json
import uuid
from loguru import logger

class Message:
    def __init__(self, content: Any, msg_type: str, priority: int = 0, ttl: Optional[int] = None):
        self.id = str(uuid.uuid4())
        self.content = content
        self.type = msg_type
        self.priority = priority
        self.created_at = datetime.utcnow()
        self.ttl = ttl  # Time to live in seconds
        self.acknowledged = False
        self.ack_time = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "type": self.type,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "ttl": self.ttl,
            "acknowledged": self.acknowledged,
            "ack_time": self.ack_time.isoformat() if self.ack_time else None
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        msg = cls(
            content=data["content"],
            msg_type=data["type"],
            priority=data["priority"],
            ttl=data["ttl"]
        )
        msg.id = data["id"]
        msg.created_at = datetime.fromisoformat(data["created_at"])
        msg.acknowledged = data["acknowledged"]
        msg.ack_time = datetime.fromisoformat(data["ack_time"]) if data["ack_time"] else None
        return msg

    def is_expired(self) -> bool:
        if not self.ttl:
            return False
        return (datetime.utcnow() - self.created_at).total_seconds() > self.ttl

class IPC_Service:
    def __init__(self, shm_size: int = 1024 * 1024):  # 1MB default
        self.SHM_SIZE = shm_size
        self.msg_queue = Queue()
        self.processing_thread = None
        self.stop_event = Event()
        self.lock = Lock()
        
        try:
            self.shm = shared_memory.SharedMemory(name="status")
            logger.info("Connected to existing shared memory")
        except FileNotFoundError:
            self.shm = shared_memory.SharedMemory(create=True, size=self.SHM_SIZE, name="status")
            logger.info("Created new shared memory block")
        
        self.start_processing()

    def send_message(self, content: Any, msg_type: str, priority: int = 0, ttl: Optional[int] = None) -> str:
        """
        Send a message with optional priority and time-to-live
        Returns the message ID
        """
        try:
            message = Message(content, msg_type, priority, ttl)
            self.msg_queue.put(message)
            logger.info(f"Message queued: {message.id}")
            return message.id
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    def acknowledge_message(self, message_id: str) -> bool:
        """Acknowledge a message by its ID"""
        try:
            with self.lock:
                # Find the message in the queue
                temp_queue = Queue()
                found = False
                
                while not self.msg_queue.empty():
                    msg = self.msg_queue.get()
                    if msg.id == message_id:
                        msg.acknowledged = True
                        msg.ack_time = datetime.utcnow()
                        found = True
                    temp_queue.put(msg)
                
                # Restore the queue
                while not temp_queue.empty():
                    self.msg_queue.put(temp_queue.get())
                
                return found
        except Exception as e:
            logger.error(f"Error acknowledging message: {e}")
            return False

    def get_message(self, message_id: Optional[str] = None) -> Optional[Message]:
        """Get a specific message by ID or the next unacknowledged message"""
        try:
            with self.lock:
                temp_queue = Queue()
                found_message = None
                
                while not self.msg_queue.empty():
                    msg = self.msg_queue.get()
                    if message_id:
                        if msg.id == message_id:
                            found_message = msg
                    elif not msg.acknowledged and not msg.is_expired():
                        found_message = msg
                    temp_queue.put(msg)
                
                # Restore the queue
                while not temp_queue.empty():
                    self.msg_queue.put(temp_queue.get())
                
                return found_message
        except Exception as e:
            logger.error(f"Error getting message: {e}")
            return None

    def start_processing(self):
        """Start the message processing thread"""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.stop_event.clear()
            self.processing_thread = Thread(target=self._process_queue, daemon=True)
            self.processing_thread.start()
            logger.info("Message processing thread started")

    def stop_processing(self):
        """Stop the message processing thread"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_event.set()
            self.processing_thread.join()
            logger.info("Message processing thread stopped")

    def _process_queue(self):
        """Process messages from the queue"""
        while not self.stop_event.is_set():
            try:
                if not self.msg_queue.empty():
                    message = self.msg_queue.get()
                    
                    # Skip expired messages
                    if message.is_expired():
                        logger.info(f"Message expired: {message.id}")
                        continue
                    
                    # Process the message
                    self._process_message(message)
                    
                    # Put the message back in the queue if not acknowledged
                    if not message.acknowledged:
                        self.msg_queue.put(message)
                
                self.stop_event.wait(0.1)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    def _process_message(self, message: Message):
        """Process a single message"""
        try:
            # Convert message to JSON
            message_data = json.dumps(message.to_dict())
            
            # Ensure message fits in shared memory
            if len(message_data.encode('utf-8')) > self.SHM_SIZE:
                logger.error(f"Message too large for shared memory: {message.id}")
                return
            
            # Write to shared memory
            with self.lock:
                data = message_data.encode('utf-8')
                self.shm.buf[:len(data)] = data
                logger.info(f"Message written to shared memory: {message.id}")
                
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")

    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_processing()
            self.shm.close()
            self.shm.unlink()  # This will delete the shared memory block
            logger.info("IPC service cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up IPC service: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Create a singleton instance
ipc_instance = IPC_Service()
        