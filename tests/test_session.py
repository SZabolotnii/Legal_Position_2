"""
Test script for session management system.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import get_settings
from src.session import (
    SessionManager,
    UserSessionState,
    generate_session_id,
    create_empty_session,
    get_session_manager
)


async def test_session_state():
    """Test UserSessionState functionality."""
    print("=" * 50)
    print("Testing UserSessionState")
    print("=" * 50)
    
    # Test session creation
    session_id = generate_session_id()
    session = create_empty_session(session_id)
    
    print(f"✅ Created session: {session}")
    assert session.session_id == session_id
    assert not session.has_legal_position()
    assert not session.has_search_results()
    
    # Test session data
    legal_position = {
        "title": "Test Position",
        "text": "Test content",
        "proceeding": "Civil",
        "category": "Contract Law"
    }
    
    session.legal_position_json = legal_position
    session.update_activity()
    
    print(f"✅ Added legal position: {session.has_legal_position()}")
    assert session.has_legal_position()
    
    # Test serialization
    session_dict = session.to_dict()
    print(f"✅ Serialized to dict: {len(session_dict)} keys")
    
    # Test deserialization
    restored_session = UserSessionState.from_dict(session_dict)
    print(f"✅ Restored from dict: {restored_session}")
    assert restored_session.session_id == session.session_id
    assert restored_session.legal_position_json == legal_position
    
    print("✅ UserSessionState tests passed!")


async def test_session_manager():
    """Test SessionManager functionality."""
    print("\n" + "=" * 50)
    print("Testing SessionManager")
    print("=" * 50)
    
    # Create session manager
    manager = SessionManager(storage_type="memory")
    print(f"✅ Created session manager: {manager}")
    
    # Test session creation
    session1 = await manager.get_session()
    print(f"✅ Created session 1: {session1}")
    
    session2 = await manager.get_session()
    print(f"✅ Created session 2: {session2}")
    
    assert session1.session_id != session2.session_id
    
    # Test session retrieval
    retrieved_session1 = await manager.get_session(session1.session_id)
    print(f"✅ Retrieved session 1: {retrieved_session1}")
    assert retrieved_session1.session_id == session1.session_id
    
    # Test session update
    retrieved_session1.legal_position_json = {"test": "data"}
    await manager.update_session(retrieved_session1)
    
    # Verify update
    updated_session = await manager.get_session(session1.session_id)
    print(f"✅ Updated session: {updated_session.has_legal_position()}")
    assert updated_session.has_legal_position()
    
    # Test session count
    session_count = await manager.get_session_count()
    print(f"✅ Session count: {session_count}")
    assert session_count >= 2
    
    # Test session deletion
    await manager.delete_session(session1.session_id)
    deleted_session = await manager.get_session(session1.session_id)
    print(f"✅ Session after deletion: {deleted_session}")
    assert deleted_session.session_id != session1.session_id  # Should create new
    
    # Test cleanup
    cleaned_count = await manager.cleanup_expired_sessions()
    print(f"✅ Cleaned sessions: {cleaned_count}")
    
    # Shutdown
    await manager.shutdown()
    print("✅ Session manager shutdown")
    
    print("✅ SessionManager tests passed!")


async def test_global_session_manager():
    """Test global session manager."""
    print("\n" + "=" * 50)
    print("Testing Global Session Manager")
    print("=" * 50)
    
    # Get global manager
    manager1 = get_session_manager()
    manager2 = get_session_manager()
    
    print(f"✅ Global manager instances: {manager1 is manager2}")
    assert manager1 is manager2  # Should be same instance
    
    # Test with global manager
    session = await manager1.get_session()
    print(f"✅ Global session: {session}")
    
    print("✅ Global session manager tests passed!")


async def main():
    """Run all session tests."""
    print("🧪 Starting Session System Tests")
    
    try:
        # Load configuration (without API key validation for testing)
        settings = get_settings(validate_api_keys=False)
        print(f"✅ Configuration loaded: {settings.app.environment}")
        
        # Run tests
        await test_session_state()
        await test_session_manager()
        await test_global_session_manager()
        
        print("\n" + "=" * 60)
        print("🎉 All session tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
