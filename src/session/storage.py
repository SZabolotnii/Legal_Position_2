"""
Session storage implementations.
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Optional
from src.session.state import UserSessionState


class BaseStorage(ABC):
    """Abstract base class for session storage."""
    
    @abstractmethod
    async def get(self, session_id: str) -> Optional[UserSessionState]:
        """Get session state by ID."""
        pass
    
    @abstractmethod
    async def set(self, session: UserSessionState) -> None:
        """Store session state."""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete session state."""
        pass
    
    @abstractmethod
    async def cleanup_expired(self, timeout_minutes: int) -> int:
        """Clean up expired sessions. Returns number of cleaned sessions."""
        pass
    
    @abstractmethod
    async def get_all_sessions(self) -> Dict[str, UserSessionState]:
        """Get all active sessions."""
        pass


class MemoryStorage(BaseStorage):
    """In-memory session storage."""
    
    def __init__(self):
        self._sessions: Dict[str, UserSessionState] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, session_id: str) -> Optional[UserSessionState]:
        """Get session state by ID."""
        async with self._lock:
            return self._sessions.get(session_id)
    
    async def set(self, session: UserSessionState) -> None:
        """Store session state."""
        async with self._lock:
            self._sessions[session.session_id] = session
    
    async def delete(self, session_id: str) -> None:
        """Delete session state."""
        async with self._lock:
            self._sessions.pop(session_id, None)
    
    async def cleanup_expired(self, timeout_minutes: int) -> int:
        """Clean up expired sessions."""
        async with self._lock:
            expired_sessions = [
                session_id for session_id, session in self._sessions.items()
                if session.is_expired(timeout_minutes)
            ]
            
            for session_id in expired_sessions:
                del self._sessions[session_id]
            
            return len(expired_sessions)
    
    async def get_all_sessions(self) -> Dict[str, UserSessionState]:
        """Get all active sessions."""
        async with self._lock:
            return self._sessions.copy()


class RedisStorage(BaseStorage):
    """Redis-based session storage."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, password: Optional[str] = None):
        try:
            import redis.asyncio as redis
            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True
            )
            self._available = True
        except ImportError:
            print("Warning: redis package not installed. Using memory storage.")
            self._available = False
            self._fallback = MemoryStorage()
    
    async def get(self, session_id: str) -> Optional[UserSessionState]:
        """Get session state by ID."""
        if not self._available:
            return await self._fallback.get(session_id)
        
        try:
            data = await self.redis.get(f"session:{session_id}")
            if data:
                import json
                session_data = json.loads(data)
                return UserSessionState.from_dict(session_data)
        except Exception as e:
            print(f"Redis error in get(): {e}")
        
        return None
    
    async def set(self, session: UserSessionState) -> None:
        """Store session state."""
        if not self._available:
            await self._fallback.set(session)
            return
        
        try:
            import json
            data = session.to_dict()
            await self.redis.set(
                f"session:{session.session_id}",
                json.dumps(data),
                ex=24 * 60 * 60  # 24 hours TTL
            )
        except Exception as e:
            print(f"Redis error in set(): {e}")
    
    async def delete(self, session_id: str) -> None:
        """Delete session state."""
        if not self._available:
            await self._fallback.delete(session_id)
            return
        
        try:
            await self.redis.delete(f"session:{session_id}")
        except Exception as e:
            print(f"Redis error in delete(): {e}")
    
    async def cleanup_expired(self, timeout_minutes: int) -> int:
        """Clean up expired sessions."""
        if not self._available:
            return await self._fallback.cleanup_expired(timeout_minutes)
        
        # Redis handles TTL automatically, so we just return 0
        # In a production system, you might want to implement
        # a more sophisticated cleanup mechanism
        return 0
    
    async def get_all_sessions(self) -> Dict[str, UserSessionState]:
        """Get all active sessions."""
        if not self._available:
            return await self._fallback.get_all_sessions()
        
        # This is not efficient for Redis, but provided for compatibility
        # In production, you might want to maintain a separate index
        try:
            keys = await self.redis.keys("session:*")
            sessions = {}
            
            import json
            for key in keys:
                session_id = key.replace("session:", "")
                data = await self.redis.get(key)
                if data:
                    session_data = json.loads(data)
                    sessions[session_id] = UserSessionState.from_dict(session_data)
            
            return sessions
        except Exception as e:
            print(f"Redis error in get_all_sessions(): {e}")
            return {}


def create_storage(storage_type: str = "memory", **kwargs) -> BaseStorage:
    """
    Factory function to create storage instance.
    
    Args:
        storage_type: Type of storage ("memory" or "redis")
        **kwargs: Additional arguments for storage initialization
        
    Returns:
        Storage instance
    """
    if storage_type == "redis":
        return RedisStorage(**kwargs)
    else:
        return MemoryStorage()
