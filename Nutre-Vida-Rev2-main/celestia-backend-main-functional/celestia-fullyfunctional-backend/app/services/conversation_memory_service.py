from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from app.models.agentic_models import ConversationMemory
import json
import uuid

class ConversationMemoryService:
    def __init__(self, db: Session):
        self.db = db
        self.max_memory_per_session = 50  # Maximum messages to keep per session
        self.memory_retention_days = 30  # Days to keep conversation memory
    
    def create_session_id(self) -> str:
        """Generate a unique session ID"""
        return str(uuid.uuid4())
    
    def store_conversation(
        self, 
        user_id: int, 
        session_id: str, 
        message_type: str, 
        content: str, 
        context_data: Dict[str, Any] = None
    ) -> ConversationMemory:
        """Store a conversation message with context"""
        try:
            # Calculate importance score based on content and context
            importance_score = self._calculate_importance_score(content, context_data or {})
            
            memory = ConversationMemory(
                user_id=user_id,
                session_id=session_id,
                message_type=message_type,
                content=content,
                context_data=context_data or {},
                importance_score=importance_score
            )
            
            self.db.add(memory)
            self.db.commit()
            self.db.refresh(memory)
            
            # Clean up old memories to maintain performance
            self._cleanup_old_memories(user_id, session_id)
            
            return memory
            
        except Exception as e:
            print(f"Error storing conversation: {e}")
            self.db.rollback()
            return None
    
    def get_session_history(
        self, 
        user_id: int, 
        session_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a specific session"""
        try:
            memories = self.db.query(ConversationMemory).filter(
                and_(
                    ConversationMemory.user_id == user_id,
                    ConversationMemory.session_id == session_id
                )
            ).order_by(ConversationMemory.created_at.desc()).limit(limit).all()
            
            # Reverse to get chronological order
            memories.reverse()
            
            return [
                {
                    'id': memory.id,
                    'message_type': memory.message_type,
                    'content': memory.content,
                    'context_data': memory.context_data,
                    'importance_score': memory.importance_score,
                    'created_at': memory.created_at.isoformat()
                }
                for memory in memories
            ]
            
        except Exception as e:
            print(f"Error retrieving session history: {e}")
            return []
    
    def get_contextual_memory(
        self, 
        user_id: int, 
        current_context: Dict[str, Any] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant conversation memories based on current context"""
        try:
            # Get recent high-importance memories
            base_query = self.db.query(ConversationMemory).filter(
                ConversationMemory.user_id == user_id
            )
            
            # Filter by recency and importance
            cutoff_date = datetime.now() - timedelta(days=self.memory_retention_days)
            memories = base_query.filter(
                and_(
                    ConversationMemory.created_at >= cutoff_date,
                    ConversationMemory.importance_score >= 0.3  # Only moderately important memories
                )
            ).order_by(
                desc(ConversationMemory.importance_score),
                desc(ConversationMemory.created_at)
            ).limit(limit * 2).all()  # Get more to filter contextually
            
            # If current context is provided, filter for relevance
            if current_context:
                relevant_memories = self._filter_by_context_relevance(memories, current_context)
                return relevant_memories[:limit]
            
            return [
                {
                    'id': memory.id,
                    'message_type': memory.message_type,
                    'content': memory.content,
                    'context_data': memory.context_data,
                    'importance_score': memory.importance_score,
                    'created_at': memory.created_at.isoformat(),
                    'session_id': memory.session_id
                }
                for memory in memories[:limit]
            ]
            
        except Exception as e:
            print(f"Error retrieving contextual memory: {e}")
            return []
    
    def search_conversation_history(
        self, 
        user_id: int, 
        search_query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search through conversation history using keywords"""
        try:
            # Simple text search (can be enhanced with full-text search later)
            search_terms = search_query.lower().split()
            
            memories = self.db.query(ConversationMemory).filter(
                ConversationMemory.user_id == user_id
            ).order_by(desc(ConversationMemory.created_at)).all()
            
            matching_memories = []
            for memory in memories:
                content_lower = memory.content.lower()
                context_str = json.dumps(memory.context_data).lower()
                
                # Check if any search term matches
                relevance_score = 0
                for term in search_terms:
                    if term in content_lower:
                        relevance_score += 2
                    if term in context_str:
                        relevance_score += 1
                
                if relevance_score > 0:
                    matching_memories.append({
                        'memory': memory,
                        'relevance_score': relevance_score
                    })
            
            # Sort by relevance and recency
            matching_memories.sort(
                key=lambda x: (x['relevance_score'], x['memory'].created_at), 
                reverse=True
            )
            
            return [
                {
                    'id': item['memory'].id,
                    'message_type': item['memory'].message_type,
                    'content': item['memory'].content,
                    'context_data': item['memory'].context_data,
                    'importance_score': item['memory'].importance_score,
                    'created_at': item['memory'].created_at.isoformat(),
                    'session_id': item['memory'].session_id,
                    'relevance_score': item['relevance_score']
                }
                for item in matching_memories[:limit]
            ]
            
        except Exception as e:
            print(f"Error searching conversation history: {e}")
            return []
    
    def get_user_conversation_summary(self, user_id: int) -> Dict[str, Any]:
        """Get a summary of user's conversation patterns and preferences"""
        try:
            # Get all memories for analysis
            cutoff_date = datetime.now() - timedelta(days=self.memory_retention_days)
            memories = self.db.query(ConversationMemory).filter(
                and_(
                    ConversationMemory.user_id == user_id,
                    ConversationMemory.created_at >= cutoff_date
                )
            ).all()
            
            if not memories:
                return {'total_conversations': 0}
            
            # Analyze conversation patterns
            total_messages = len(memories)
            user_messages = [m for m in memories if m.message_type == 'user']
            agent_messages = [m for m in memories if m.message_type == 'agent']
            
            # Extract common topics from context data
            topics = {}
            food_mentions = set()
            goal_mentions = set()
            
            for memory in memories:
                context = memory.context_data
                
                # Extract topics from context
                if context.get('current_analysis'):
                    items = context['current_analysis'].get('items', [])
                    for item in items:
                        food_name = item.get('name', '').lower()
                        if food_name:
                            food_mentions.add(food_name)
                
                # Extract goals mentioned
                if context.get('user_context', {}).get('goals'):
                    for goal in context['user_context']['goals']:
                        goal_mentions.add(goal.lower())
                
                # Count topic frequencies in content
                content_lower = memory.content.lower()
                topic_keywords = ['nutrition', 'calories', 'protein', 'exercise', 'weight', 'health', 'diet']
                for keyword in topic_keywords:
                    if keyword in content_lower:
                        topics[keyword] = topics.get(keyword, 0) + 1
            
            # Calculate engagement metrics
            avg_importance = sum(m.importance_score for m in memories) / len(memories)
            high_importance_count = len([m for m in memories if m.importance_score >= 0.7])
            
            # Get session statistics
            unique_sessions = len(set(m.session_id for m in memories))
            avg_messages_per_session = total_messages / unique_sessions if unique_sessions > 0 else 0
            
            return {
                'total_conversations': total_messages,
                'user_messages': len(user_messages),
                'agent_messages': len(agent_messages),
                'unique_sessions': unique_sessions,
                'avg_messages_per_session': round(avg_messages_per_session, 1),
                'avg_importance_score': round(avg_importance, 2),
                'high_importance_conversations': high_importance_count,
                'common_topics': dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]),
                'frequently_mentioned_foods': list(food_mentions)[:10],
                'mentioned_goals': list(goal_mentions),
                'conversation_period_days': self.memory_retention_days,
                'last_conversation': memories[-1].created_at.isoformat() if memories else None
            }
            
        except Exception as e:
            print(f"Error generating conversation summary: {e}")
            return {'error': str(e)}
    
    def _calculate_importance_score(self, content: str, context_data: Dict[str, Any]) -> float:
        """Calculate importance score for a conversation message"""
        score = 0.0
        content_lower = content.lower()
        
        # Base score for all messages
        score += 0.1
        
        # Higher score for questions
        if '?' in content:
            score += 0.2
        
        # Higher score for goal-related content
        goal_keywords = ['goal', 'target', 'want to', 'trying to', 'plan to']
        if any(keyword in content_lower for keyword in goal_keywords):
            score += 0.3
        
        # Higher score for health concerns
        health_keywords = ['problem', 'issue', 'concern', 'worried', 'help']
        if any(keyword in content_lower for keyword in health_keywords):
            score += 0.3
        
        # Higher score for specific food preferences or restrictions
        restriction_keywords = ['allergic', 'vegetarian', 'vegan', 'avoid', 'cannot eat']
        if any(keyword in content_lower for keyword in restriction_keywords):
            score += 0.4
        
        # Context-based scoring
        if context_data:
            # Higher score if meal analysis is present
            if context_data.get('current_analysis'):
                score += 0.2
            
            # Higher score for goal-related context
            if context_data.get('user_context', {}).get('goals'):
                score += 0.2
            
            # Higher score for nutritional insights
            if context_data.get('nutritional_gaps') or context_data.get('meal_improvements'):
                score += 0.2
        
        # Cap the score at 1.0
        return min(score, 1.0)
    
    def _filter_by_context_relevance(
        self, 
        memories: List[ConversationMemory], 
        current_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter memories by relevance to current context"""
        relevant_memories = []
        
        # Extract current context keywords
        current_keywords = set()
        
        if current_context.get('current_analysis'):
            items = current_context['current_analysis'].get('items', [])
            for item in items:
                food_name = item.get('name', '').lower()
                current_keywords.update(food_name.split())
        
        if current_context.get('user_context', {}).get('goals'):
            for goal in current_context['user_context']['goals']:
                current_keywords.update(goal.lower().split())
        
        for memory in memories:
            relevance_score = 0
            
            # Check content relevance
            memory_content = memory.content.lower()
            memory_context = json.dumps(memory.context_data).lower()
            
            for keyword in current_keywords:
                if keyword in memory_content:
                    relevance_score += 2
                if keyword in memory_context:
                    relevance_score += 1
            
            # Include if relevant or high importance
            if relevance_score > 0 or memory.importance_score >= 0.7:
                relevant_memories.append({
                    'id': memory.id,
                    'message_type': memory.message_type,
                    'content': memory.content,
                    'context_data': memory.context_data,
                    'importance_score': memory.importance_score,
                    'created_at': memory.created_at.isoformat(),
                    'session_id': memory.session_id,
                    'relevance_score': relevance_score
                })
        
        # Sort by relevance and importance
        relevant_memories.sort(
            key=lambda x: (x['relevance_score'], x['importance_score']), 
            reverse=True
        )
        
        return relevant_memories
    
    def _cleanup_old_memories(self, user_id: int, session_id: str):
        """Clean up old memories to maintain performance"""
        try:
            # Remove very old memories
            cutoff_date = datetime.now() - timedelta(days=self.memory_retention_days)
            old_memories = self.db.query(ConversationMemory).filter(
                and_(
                    ConversationMemory.user_id == user_id,
                    ConversationMemory.created_at < cutoff_date
                )
            ).all()
            
            for memory in old_memories:
                self.db.delete(memory)
            
            # Limit memories per session
            session_memories = self.db.query(ConversationMemory).filter(
                and_(
                    ConversationMemory.user_id == user_id,
                    ConversationMemory.session_id == session_id
                )
            ).order_by(desc(ConversationMemory.created_at)).all()
            
            if len(session_memories) > self.max_memory_per_session:
                # Keep high importance memories and recent ones
                to_keep = []
                to_delete = []
                
                for memory in session_memories:
                    if len(to_keep) < self.max_memory_per_session:
                        if memory.importance_score >= 0.5 or len(to_keep) < self.max_memory_per_session // 2:
                            to_keep.append(memory)
                        else:
                            to_delete.append(memory)
                    else:
                        to_delete.append(memory)
                
                for memory in to_delete:
                    self.db.delete(memory)
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error cleaning up memories: {e}")
            self.db.rollback()
    
    def update_memory_importance(self, memory_id: int, new_importance: float):
        """Update the importance score of a specific memory"""
        try:
            memory = self.db.query(ConversationMemory).filter(
                ConversationMemory.id == memory_id
            ).first()
            
            if memory:
                memory.importance_score = min(max(new_importance, 0.0), 1.0)
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error updating memory importance: {e}")
            self.db.rollback()
            return False
