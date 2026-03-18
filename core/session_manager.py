# Session manager service
import logging
import time
from typing import Dict, Any, List

class SessionManager:
    """会话管理服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sessions = {}
        self.session_timeout = 3600  # 会话超时时间（秒）
    
    def create_session(self, session_id: str, user_id: str, channel_id: str):
        """创建会话"""
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "channel_id": channel_id,
            "created_at": time.time(),
            "last_updated": time.time(),
            "messages": [],
            "context": {}
        }
        
        self.sessions[session_id] = session
        self.logger.info(f"Session {session_id} created for user {user_id} on channel {channel_id}")
        return session
    
    def get_session(self, session_id: str):
        """获取会话"""
        if session_id not in self.sessions:
            self.logger.warning(f"Session {session_id} not found")
            return None
        
        session = self.sessions[session_id]
        # 检查会话是否超时
        if time.time() - session["last_updated"] > self.session_timeout:
            self.logger.info(f"Session {session_id} timed out")
            del self.sessions[session_id]
            return None
        
        # 更新最后更新时间
        session["last_updated"] = time.time()
        return session
    
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """更新会话"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.update(updates)
        session["last_updated"] = time.time()
        self.logger.info(f"Session {session_id} updated")
        return True
    
    def add_message(self, session_id: str, message: Dict[str, Any]):
        """添加消息到会话"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["messages"].append(message)
        session["last_updated"] = time.time()
        self.logger.info(f"Message added to session {session_id}")
        return True
    
    def get_session_messages(self, session_id: str):
        """获取会话消息"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session["messages"]
    
    def set_session_context(self, session_id: str, context: Dict[str, Any]):
        """设置会话上下文"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["context"] = context
        session["last_updated"] = time.time()
        self.logger.info(f"Context set for session {session_id}")
        return True
    
    def get_session_context(self, session_id: str):
        """获取会话上下文"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return session["context"]
    
    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Session {session_id} deleted")
            return True
        else:
            self.logger.warning(f"Session {session_id} not found")
            return False
    
    def get_user_sessions(self, user_id: str):
        """获取用户的所有会话"""
        user_sessions = []
        for session_id, session in self.sessions.items():
            if session["user_id"] == user_id:
                user_sessions.append(session)
        return user_sessions
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        expired_sessions = []
        current_time = time.time()
        
        for session_id, session in self.sessions.items():
            if current_time - session["last_updated"] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            self.logger.info(f"Expired session {session_id} cleaned up")
        
        return len(expired_sessions)
