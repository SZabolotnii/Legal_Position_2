"""
Session manager for handling user sessions.
"""
import asyncio
import uuid
from typing import Dict, Optional
from config import get_settings
from src.session.state import UserSessionState, generate_session_id
from src.session.storage import create_storage, BaseStorage


class SessionManager:
    """
    Manages user sessions with isolation.
    
    This class ensures that each user has their own isolated session state,
    which is critical for multi-user environments like Hugging Face Spaces.
    """
    
    def __init__(self, storage_type: str = "memory", **storage_kwargs):
        """
        Initialize the session manager.
        
        Args:
            storage_type: Type of storage ("memory" or "redis")
            **storage_kwargs: Additional arguments for storage initialization
        """
        self.storage: BaseStorage = create_storage(storage_type, **storage_kwargs)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # Don't start cleanup task here — no event loop may be running yet.
        # It will be started lazily on first get_session() call.
    
    def _start_cleanup_task(self) -> None:
        """Start the background cleanup task (only if inside a running event loop)."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop — skip, will retry on next get_session()
            return
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = loop.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired sessions."""
        try:
            settings = get_settings()
            cleanup_interval = settings.session.cleanup_interval_minutes
            
            while True:
                try:
                    await asyncio.sleep(cleanup_interval * 60)  # Convert to seconds
                    
                    timeout_minutes = settings.session.timeout_minutes
                    cleaned_count = await self.storage.cleanup_expired(timeout_minutes)
                    
                    if cleaned_count > 0:
                        print(f"Cleaned up {cleaned_count} expired sessions")
                        
                except Exception as e:
                    print(f"Error in session cleanup: {e}")
                    await asyncio.sleep(60)  # Wait a minute before retrying
                    
        except asyncio.CancelledError:
            print("Session cleanup task cancelled")
            raise
    
    async def get_session(self, session_id: Optional[str] = None) -> UserSessionState:
        """
        Get or create a user session.
        
        Args:
            session_id: Existing session ID, or None to create new
            
        Returns:
            UserSessionState instance
        """
        # Lazily start cleanup task now that we're inside a running event loop
        self._start_cleanup_task()
        
        async with self._lock:
            if session_id is None:
                session_id = generate_session_id()
            
            # Try to get existing session
            session = await self.storage.get(session_id)
            
            if session is None:
                # Create new session
                session = UserSessionState(session_id=session_id)
                await self.storage.set(session)
                print(f"Created new session: {session_id}")
            else:
                # Update activity timestamp
                session.update_activity()
                await self.storage.set(session)
            
            return session
    
    async def update_session(self, session: UserSessionState) -> None:
        """
        Update session data in storage.
        
        Args:
            session: Session to update
        """
        async with self._lock:
            session.update_activity()
            await self.storage.set(session)
    
    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session.
        
        Args:
            session_id: ID of session to delete
        """
        async with self._lock:
            await self.storage.delete(session_id)
            print(f"Deleted session: {session_id}")
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Manually trigger cleanup of expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        async with self._lock:
            settings = get_settings()
            timeout_minutes = settings.session.timeout_minutes
            cleaned_count = await self.storage.cleanup_expired(timeout_minutes)
            
            if cleaned_count > 0:
                print(f"Manually cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count
    
    async def get_all_sessions(self) -> Dict[str, UserSessionState]:
        """
        Get all active sessions (for monitoring/debugging).
        
        Returns:
            Dictionary of session_id -> UserSessionState
        """
        async with self._lock:
            return await self.storage.get_all_sessions()
    
    async def get_session_count(self) -> int:
        """
        Get the total number of active sessions.
        
        Returns:
            Number of active sessions
        """
        sessions = await self.get_all_sessions()
        return len(sessions)
    
    async def shutdown(self) -> None:
        """Shutdown the session manager and cleanup resources."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        print("Session manager shutdown complete")
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"SessionManager(storage_type={type(self.storage).__name__})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return self.__str__()


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager instance."""
    global _session_manager
    
    if _session_manager is None:
        settings = get_settings()
        
        # Configure storage based on settings
        storage_kwargs = {}
        if settings.session.storage_type == "redis":
            storage_kwargs.update({
                "host": settings.redis.host,
                "port": settings.redis.port,
                "db": settings.redis.db,
                "password": settings.redis.password,
            })
        
        _session_manager = SessionManager(
            storage_type=settings.session.storage_type,
            **storage_kwargs
        )
    
    return _session_manager


async def create_user_session() -> UserSessionState:
    """
    Create a new user session.
    
    Returns:
        New UserSessionState instance
    """
    manager = get_session_manager()
    return await manager.get_session()


async def get_user_session(session_id: str) -> UserSessionState:
    """
    Get an existing user session.
    
    Args:
        session_id: Session ID
        
    Returns:
        UserSessionState instance
    """
    manager = get_session_manager()
    return await manager.get_session(session_id)
