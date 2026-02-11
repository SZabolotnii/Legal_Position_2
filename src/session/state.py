"""
User session state management.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from llama_index.core.schema import NodeWithScore


@dataclass
class UserSessionState:
    """
    Isolated state for each user session.

    This class encapsulates all the state that needs to be maintained
    separately for each user in a multi-user environment.
    """
    session_id: str
    legal_position_json: Optional[Dict[str, Any]] = None
    search_nodes: Optional[List[NodeWithScore]] = None
    custom_prompts: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int) -> bool:
        """
        Check if the session has expired.
        
        Args:
            timeout_minutes: Session timeout in minutes
            
        Returns:
            True if session has expired
        """
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.now() - self.last_activity > timeout
    
    def get_age_minutes(self) -> float:
        """
        Get the age of the session in minutes.
        
        Returns:
            Age in minutes since creation
        """
        return (datetime.now() - self.created_at).total_seconds() / 60
    
    def get_idle_minutes(self) -> float:
        """
        Get the idle time of the session in minutes.
        
        Returns:
            Idle time in minutes since last activity
        """
        return (datetime.now() - self.last_activity).total_seconds() / 60
    
    def clear_data(self) -> None:
        """Clear all user data but keep session metadata."""
        self.legal_position_json = None
        self.search_nodes = None
        self.custom_prompts = {}
        self.update_activity()
    
    def has_legal_position(self) -> bool:
        """Check if user has generated a legal position."""
        return self.legal_position_json is not None
    
    def has_search_results(self) -> bool:
        """Check if user has search results."""
        return self.search_nodes is not None and len(self.search_nodes) > 0

    def get_prompt(self, prompt_type: str, default_prompt: str) -> str:
        """
        Get custom prompt or default if not set.

        Args:
            prompt_type: Type of prompt ('system', 'legal_position', 'analysis')
            default_prompt: Default prompt value

        Returns:
            Custom prompt if set, otherwise default
        """
        return self.custom_prompts.get(prompt_type, default_prompt)

    def set_prompt(self, prompt_type: str, prompt_value: str) -> None:
        """
        Set custom prompt.

        Args:
            prompt_type: Type of prompt ('system', 'legal_position', 'analysis')
            prompt_value: Prompt text
        """
        self.custom_prompts[prompt_type] = prompt_value
        self.update_activity()

    def reset_prompts(self) -> None:
        """Reset all custom prompts to defaults."""
        self.custom_prompts = {}
        self.update_activity()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session to dictionary for storage.
        
        Returns:
            Dictionary representation
        """
        # Convert NodeWithScore objects to serializable format
        search_nodes_data = None
        if self.search_nodes:
            search_nodes_data = [
                {
                    "node": {
                        "id": node.node.id_,
                        "text": node.node.text,
                        "metadata": node.node.metadata,
                    },
                    "score": node.score,
                }
                for node in self.search_nodes
            ]
        
        return {
            "session_id": self.session_id,
            "legal_position_json": self.legal_position_json,
            "search_nodes": search_nodes_data,
            "custom_prompts": self.custom_prompts,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSessionState':
        """
        Create session from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            UserSessionState instance
        """
        # Convert back to NodeWithScore objects
        search_nodes = None
        if data.get("search_nodes"):
            from llama_index.core.schema import Document, NodeWithScore
            
            search_nodes = []
            for item in data["search_nodes"]:
                node_data = item["node"]
                document = Document(
                    id_=node_data["id"],
                    text=node_data["text"],
                    metadata=node_data["metadata"],
                )
                node_with_score = NodeWithScore(
                    node=document,
                    score=item["score"]
                )
                search_nodes.append(node_with_score)
        
        return cls(
            session_id=data["session_id"],
            legal_position_json=data["legal_position_json"],
            search_nodes=search_nodes,
            custom_prompts=data.get("custom_prompts", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
        )
    
    def __str__(self) -> str:
        """String representation."""
        return (
            f"UserSessionState("
            f"session_id={self.session_id[:8]}..., "
            f"age={self.get_age_minutes():.1f}min, "
            f"idle={self.get_idle_minutes():.1f}min, "
            f"has_position={self.has_legal_position()}, "
            f"has_search={self.has_search_results()}"
            f")"
        )
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return self.__str__()


def generate_session_id() -> str:
    """
    Generate a unique session ID.
    
    Returns:
        Unique session identifier
    """
    return str(uuid.uuid4())


def create_empty_session(session_id: Optional[str] = None) -> UserSessionState:
    """
    Create an empty session.
    
    Args:
        session_id: Optional session ID, generated if not provided
        
    Returns:
        New empty UserSessionState
    """
    if session_id is None:
        session_id = generate_session_id()
    
    return UserSessionState(session_id=session_id)
