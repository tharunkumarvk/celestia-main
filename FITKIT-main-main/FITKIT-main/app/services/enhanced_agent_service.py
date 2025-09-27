from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import google.generativeai as genai
from app.config import settings
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.health_monitoring_service import HealthMonitoringService
from app.services.smart_notification_service import SmartNotificationService
from app.services.intelligent_meal_planner import IntelligentMealPlanner
from app.services.agent_service import HealthCoachAgent
import json
import uuid

# Configure Gemini AI
genai.configure(api_key=settings.google_api_key)
enhanced_agent_model = genai.GenerativeModel("models/gemini-2.0-flash")

class EnhancedAgenticService:
    """
    Enhanced Agentic AI Service that integrates all advanced AI capabilities:
    - Contextual conversation memory across sessions
    - Proactive health monitoring with alerts
    - Smart notifications for meal timing
    - Intelligent meal planning
    - Predictive health analytics
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize all agentic services
        self.conversation_memory = ConversationMemoryService(db)
        self.health_monitor = HealthMonitoringService(db)
        self.notification_service = SmartNotificationService(db)
        self.meal_planner = IntelligentMealPlanner(db)
        self.base_agent = HealthCoachAgent(db)
        
        # Session management
        self.active_sessions = {}  # Store active conversation sessions
    
    async def enhanced_chat(
        self, 
        user_id: int, 
        message: str, 
        session_id: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Enhanced chat with full agentic capabilities including memory, 
        proactive monitoring, and intelligent responses
        """
        try:
            # Get or create session
            if not session_id:
                session_id = self.conversation_memory.create_session_id()
            
            # Store user message in conversation memory
            user_context = context or {}
            memory_entry = self.conversation_memory.store_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type='user',
                content=message,
                context_data=user_context
            )
            
            # Get contextual memory for enhanced responses
            contextual_memories = self.conversation_memory.get_contextual_memory(
                user_id=user_id,
                current_context=user_context,
                limit=5
            )
            
            # Run proactive health monitoring
            monitoring_results = self.health_monitor.run_health_monitoring(user_id)
            
            # Check for any urgent alerts
            active_alerts = self.health_monitor.get_active_alerts(user_id)
            urgent_alerts = [alert for alert in active_alerts if alert['severity'] in ['high', 'critical']]
            
            # Generate enhanced response using all available context
            enhanced_context = {
                **user_context,
                'conversation_history': contextual_memories,
                'health_alerts': active_alerts,
                'monitoring_insights': monitoring_results,
                'session_id': session_id
            }
            
            # Generate AI response
            agent_response = await self._generate_enhanced_response(
                user_id=user_id,
                message=message,
                context=enhanced_context
            )
            
            # Store agent response in conversation memory
            self.conversation_memory.store_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type='agent',
                content=agent_response['message'],
                context_data={
                    'response_type': agent_response.get('response_type', 'general'),
                    'confidence': agent_response.get('confidence', 0.8),
                    'actions_suggested': agent_response.get('actions', [])
                }
            )
            
            # Generate smart notifications if appropriate
            if agent_response.get('trigger_notifications', False):
                notification_results = self.notification_service.generate_smart_notifications(user_id)
            else:
                notification_results = {'notifications_generated': 0}
            
            # Check if meal planning is needed
            meal_plan_suggestion = None
            if self._should_suggest_meal_planning(message, user_context):
                meal_plan_suggestion = self._generate_meal_plan_suggestion(user_id)
            
            return {
                'message': agent_response['message'],
                'response_type': agent_response.get('response_type', 'general'),
                'session_id': session_id,
                'contextual_insights': {
                    'memories_used': len(contextual_memories),
                    'health_alerts': len(active_alerts),
                    'urgent_alerts': len(urgent_alerts),
                    'monitoring_completed': monitoring_results.get('monitoring_completed', False)
                },
                'proactive_features': {
                    'notifications_generated': notification_results.get('notifications_generated', 0),
                    'meal_plan_suggested': meal_plan_suggestion is not None,
                    'health_insights': monitoring_results.get('insights_generated', 0)
                },
                'suggested_actions': agent_response.get('actions', []),
                'meal_plan_suggestion': meal_plan_suggestion,
                'urgent_alerts': urgent_alerts,
                'confidence': agent_response.get('confidence', 0.8),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in enhanced chat: {e}")
            return {
                'message': "I'm having trouble processing that right now. Could you try again?",
                'response_type': 'error',
                'session_id': session_id or 'unknown',
                'error': str(e)
            }
    
    async def _generate_enhanced_response(
        self, 
        user_id: int, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate enhanced AI response using all available context"""
        
        # Build comprehensive prompt with all context
        prompt = self._build_enhanced_prompt(user_id, message, context)
        
        try:
            # Generate response using AI
            response = enhanced_agent_model.generate_content(prompt)
            response_text = response.text
            
            # Analyze response for actions and insights
            response_analysis = self._analyze_response(response_text, context)
            
            return {
                'message': response_text,
                'response_type': response_analysis.get('type', 'general'),
                'confidence': response_analysis.get('confidence', 0.8),
                'actions': response_analysis.get('actions', []),
                'trigger_notifications': response_analysis.get('trigger_notifications', False)
            }
            
        except Exception as e:
            print(f"Error generating enhanced response: {e}")
            # Fallback to base agent
            fallback_response = await self.base_agent.chat(message, context)
            return {
                'message': fallback_response,
                'response_type': 'fallback',
                'confidence': 0.6,
                'actions': []
            }
    
    def _build_enhanced_prompt(self, user_id: int, message: str, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt with all available context"""
        
        conversation_history = context.get('conversation_history', [])
        health_alerts = context.get('health_alerts', [])
        monitoring_insights = context.get('monitoring_insights', {})
        
        prompt = f"""
        You are an advanced AI Health Coach with comprehensive knowledge of the user's health journey.
        You have access to conversation memory, health monitoring data, and predictive insights.
        
        CONVERSATION CONTEXT:
        Recent conversation history:
        {self._format_conversation_history(conversation_history)}
        
        HEALTH MONITORING INSIGHTS:
        Active alerts: {len(health_alerts)}
        Recent monitoring: {json.dumps(monitoring_insights.get('alerts', [])[:3], indent=2)}
        Health patterns detected: {json.dumps(monitoring_insights.get('patterns', [])[:2], indent=2)}
        
        CURRENT USER MESSAGE: {message}
        
        CURRENT MEAL CONTEXT:
        {json.dumps(context.get('current_analysis', {}), indent=2) if context.get('current_analysis') else 'No current meal analysis'}
        
        RESPONSE GUIDELINES:
        1. Use conversation memory to provide personalized, contextual responses
        2. Reference previous conversations when relevant
        3. Proactively address any health alerts or concerns
        4. Provide actionable, specific advice based on their patterns
        5. Be encouraging and supportive while being informative
        6. Keep responses concise but comprehensive
        7. If there are urgent health alerts, prioritize addressing them
        
        RESPONSE FORMAT:
        Provide a natural, conversational response that:
        - Acknowledges their message and any relevant history
        - Addresses health concerns proactively if present
        - Gives specific, actionable advice
        - Encourages continued engagement with their health journey
        
        Remember: You have deep knowledge of their health patterns, preferences, and goals.
        Use this to provide truly personalized guidance.
        """
        
        return prompt
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for prompt"""
        if not history:
            return "No previous conversation history"
        
        formatted = []
        for memory in history[-3:]:  # Last 3 exchanges
            formatted.append(f"- {memory['message_type'].title()}: {memory['content'][:100]}...")
        
        return "\n".join(formatted)
    
    def _analyze_response(self, response_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the generated response for type, confidence, and actions"""
        
        response_lower = response_text.lower()
        analysis = {
            'type': 'general',
            'confidence': 0.8,
            'actions': [],
            'trigger_notifications': False
        }
        
        # Determine response type
        if any(word in response_lower for word in ['alert', 'concern', 'warning', 'urgent']):
            analysis['type'] = 'health_alert'
            analysis['confidence'] = 0.9
        elif any(word in response_lower for word in ['plan', 'schedule', 'meal planning']):
            analysis['type'] = 'meal_planning'
            analysis['trigger_notifications'] = True
        elif any(word in response_lower for word in ['goal', 'target', 'progress']):
            analysis['type'] = 'goal_tracking'
        elif any(word in response_lower for word in ['reminder', 'remember', 'don\'t forget']):
            analysis['type'] = 'reminder'
            analysis['trigger_notifications'] = True
        
        # Extract suggested actions
        if 'try' in response_lower or 'consider' in response_lower:
            analysis['actions'].append('dietary_adjustment')
        if 'track' in response_lower or 'log' in response_lower:
            analysis['actions'].append('meal_tracking')
        if 'plan' in response_lower:
            analysis['actions'].append('meal_planning')
        
        return analysis
    
    def _should_suggest_meal_planning(self, message: str, context: Dict[str, Any]) -> bool:
        """Determine if meal planning should be suggested"""
        message_lower = message.lower()
        
        # Suggest meal planning if user asks about planning or goals
        planning_keywords = ['plan', 'meal plan', 'what should i eat', 'help me plan', 'weekly meals']
        if any(keyword in message_lower for keyword in planning_keywords):
            return True
        
        # Suggest if user has goal-related queries
        goal_keywords = ['goal', 'target', 'lose weight', 'gain weight', 'healthy eating']
        if any(keyword in message_lower for keyword in goal_keywords):
            return True
        
        return False
    
    def _generate_meal_plan_suggestion(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Generate a meal plan suggestion"""
        try:
            # Check if user already has an active meal plan
            existing_plans = self.meal_planner.get_user_meal_plans(user_id, active_only=True)
            
            if existing_plans:
                return {
                    'type': 'existing_plan',
                    'message': 'You already have an active meal plan. Would you like to view it or create a new one?',
                    'existing_plan': existing_plans[0]
                }
            
            return {
                'type': 'new_plan_suggestion',
                'message': 'I can create a personalized meal plan for you based on your goals and preferences. Would you like me to generate one?',
                'benefits': [
                    'Personalized to your dietary preferences',
                    'Aligned with your health goals',
                    'Based on your eating patterns',
                    'Includes variety and nutrition balance'
                ]
            }
            
        except Exception as e:
            print(f"Error generating meal plan suggestion: {e}")
            return None
    
    def get_user_health_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive health dashboard with all agentic insights"""
        try:
            # Get conversation summary
            conversation_summary = self.conversation_memory.get_user_conversation_summary(user_id)
            
            # Get active alerts
            active_alerts = self.health_monitor.get_active_alerts(user_id)
            
            # Get pending notifications
            pending_notifications = self.notification_service.get_pending_notifications(user_id)
            
            # Get meal plans
            meal_plans = self.meal_planner.get_user_meal_plans(user_id, active_only=True)
            
            # Run health monitoring for latest insights
            monitoring_results = self.health_monitor.run_health_monitoring(user_id)
            
            return {
                'user_id': user_id,
                'dashboard_generated_at': datetime.now().isoformat(),
                'conversation_insights': {
                    'total_conversations': conversation_summary.get('total_conversations', 0),
                    'engagement_score': conversation_summary.get('avg_importance_score', 0),
                    'common_topics': conversation_summary.get('common_topics', {}),
                    'last_conversation': conversation_summary.get('last_conversation')
                },
                'health_monitoring': {
                    'active_alerts': len(active_alerts),
                    'urgent_alerts': len([a for a in active_alerts if a['severity'] in ['high', 'critical']]),
                    'recent_insights': monitoring_results.get('insights_generated', 0),
                    'patterns_updated': monitoring_results.get('patterns_updated', 0)
                },
                'smart_notifications': {
                    'pending_notifications': len(pending_notifications),
                    'next_notification': pending_notifications[0] if pending_notifications else None
                },
                'meal_planning': {
                    'active_plans': len(meal_plans),
                    'current_plan': meal_plans[0] if meal_plans else None,
                    'adherence_score': meal_plans[0]['adherence_score'] if meal_plans else 0
                },
                'alerts': active_alerts[:5],  # Top 5 alerts
                'recommendations': self._generate_dashboard_recommendations(
                    conversation_summary, active_alerts, meal_plans
                )
            }
            
        except Exception as e:
            print(f"Error generating health dashboard: {e}")
            return {'error': str(e)}
    
    def _generate_dashboard_recommendations(
        self, 
        conversation_summary: Dict[str, Any], 
        alerts: List[Dict[str, Any]], 
        meal_plans: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate personalized recommendations for the dashboard"""
        recommendations = []
        
        # Conversation-based recommendations
        if conversation_summary.get('total_conversations', 0) < 5:
            recommendations.append({
                'type': 'engagement',
                'title': 'Start Your Health Journey',
                'message': 'Chat with me more to get personalized insights and recommendations!',
                'priority': 'medium'
            })
        
        # Alert-based recommendations
        urgent_alerts = [a for a in alerts if a['severity'] in ['high', 'critical']]
        if urgent_alerts:
            recommendations.append({
                'type': 'health_alert',
                'title': 'Address Health Concerns',
                'message': f'You have {len(urgent_alerts)} urgent health alerts that need attention.',
                'priority': 'high'
            })
        
        # Meal planning recommendations
        if not meal_plans:
            recommendations.append({
                'type': 'meal_planning',
                'title': 'Create a Meal Plan',
                'message': 'A personalized meal plan can help you achieve your health goals more effectively.',
                'priority': 'medium'
            })
        elif meal_plans and meal_plans[0]['adherence_score'] < 70:
            recommendations.append({
                'type': 'adherence',
                'title': 'Improve Meal Plan Adherence',
                'message': 'Your current adherence is below 70%. Let\'s discuss ways to make your meal plan more practical.',
                'priority': 'medium'
            })
        
        return recommendations
    
    def create_intelligent_meal_plan(
        self, 
        user_id: int, 
        plan_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create an intelligent meal plan using the meal planner service"""
        try:
            plan_type = plan_preferences.get('plan_type', 'weekly') if plan_preferences else 'weekly'
            duration_days = plan_preferences.get('duration_days', 7) if plan_preferences else 7
            specific_goals = plan_preferences.get('goals') if plan_preferences else None
            
            result = self.meal_planner.generate_meal_plan(
                user_id=user_id,
                plan_type=plan_type,
                duration_days=duration_days,
                specific_goals=specific_goals
            )
            
            # Generate notifications for the new meal plan
            if not result.get('error'):
                self.notification_service.generate_smart_notifications(user_id)
            
            return result
            
        except Exception as e:
            print(f"Error creating intelligent meal plan: {e}")
            return {'error': str(e)}
    
    def get_conversation_insights(self, user_id: int) -> Dict[str, Any]:
        """Get detailed conversation insights and patterns"""
        try:
            summary = self.conversation_memory.get_user_conversation_summary(user_id)
            
            # Get recent contextual memories
            recent_memories = self.conversation_memory.get_contextual_memory(
                user_id=user_id,
                limit=10
            )
            
            return {
                'conversation_summary': summary,
                'recent_important_conversations': recent_memories,
                'insights': {
                    'engagement_level': 'high' if summary.get('total_conversations', 0) > 20 else 'medium' if summary.get('total_conversations', 0) > 5 else 'low',
                    'consistency': 'regular' if summary.get('unique_sessions', 0) > 3 else 'occasional',
                    'focus_areas': list(summary.get('common_topics', {}).keys())[:3]
                }
            }
            
        except Exception as e:
            print(f"Error getting conversation insights: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, days_old: int = 30):
        """Clean up old data across all services"""
        try:
            # Clean up old notifications
            notifications_cleaned = self.notification_service.cleanup_old_notifications(days_old)
            
            # Note: Conversation memory and health monitoring have their own cleanup mechanisms
            # that run automatically, but could be triggered here if needed
            
            return {
                'cleanup_completed': True,
                'notifications_cleaned': notifications_cleaned,
                'cleanup_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            return {'error': str(e)}
