"""
Session management package for user isolation.
"""
from src.session.state import (
    UserSessionState,
    generate_session_id,
    create_empty_session,
)
from src.session.manager import (
    SessionManager,
    get_session_manager,
    create_user_session,
    get_user_session,
)
from src.session.storage import (
    BaseStorage,
    MemoryStorage,
    RedisStorage,
    create_storage,
)

__all__ = [
    # State management
    'UserSessionState',
    'generate_session_id',
    'create_empty_session',
    # Session management
    'SessionManager',
    'get_session_manager',
    'create_user_session',
    'get_user_session',
    # Storage
    'BaseStorage',
    'MemoryStorage',
    'RedisStorage',
    'create_storage',
]
