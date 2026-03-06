import { AnimatePresence, motion } from 'framer-motion';
import {
    Bot,
    Lightbulb,
    Maximize2,
    MessageCircle,
    Minimize2,
    Send,
    User,
    X
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import styled from 'styled-components';
import { useApp } from '../../App';
import renderSafe from '../../utils/renderSafe';

const ChatBotContainer = styled.div`
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
`;

const ChatBotButton = styled(motion.button)`
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  &:hover::before {
    opacity: 1;
  }
  
  svg {
    position: relative;
    z-index: 1;
  }
`;

const PulseRing = styled(motion.div)`
  position: absolute;
  top: -5px;
  left: -5px;
  right: -5px;
  bottom: -5px;
  border: 2px solid rgba(102, 126, 234, 0.6);
  border-radius: 50%;
  pointer-events: none;
`;

const ChatWindow = styled(motion.div)`
  position: absolute;
  bottom: 80px;
  right: 0;
  width: 380px;
  height: ${props => props.minimized ? '60px' : '500px'};
  background: rgba(15, 15, 35, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  @media (max-width: 480px) {
    width: calc(100vw - 40px);
    right: -20px;
  }
`;

const ChatHeader = styled.div`
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: white;
  flex-shrink: 0;
`;

const ChatHeaderLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const ChatHeaderTitle = styled.div`
  display: flex;
  flex-direction: column;
`;

const ChatTitle = styled.h3`
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  font-family: 'Orbitron', monospace;
`;

const ChatSubtitle = styled.p`
  margin: 0;
  font-size: 0.8rem;
  opacity: 0.9;
`;

const ChatHeaderButtons = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const HeaderButton = styled.button`
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 6px;
  padding: 6px;
  cursor: pointer;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
`;

const ChatMessages = styled.div`
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(102, 126, 234, 0.5);
    border-radius: 2px;
  }
`;

const Message = styled(motion.div)`
  display: flex;
  align-items: flex-start;
  gap: 12px;
  ${props => props.isUser && 'flex-direction: row-reverse;'}
`;

const MessageAvatar = styled.div`
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: ${props => props.isUser
    ? 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)'
    : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  };
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
`;

const MessageBubble = styled.div`
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  background: ${props => props.isUser
    ? 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)'
    : 'rgba(255, 255, 255, 0.1)'
  };
  color: white;
  font-size: 0.9rem;
  line-height: 1.4;
  word-wrap: break-word;
  
  ${props => props.isUser && `
    border-bottom-right-radius: 4px;
  `}
  
  ${props => !props.isUser && `
    border-bottom-left-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.1);
  `}
`;

const ChatInput = styled.div`
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 12px;
  align-items: center;
  flex-shrink: 0;
`;

const InputField = styled.input`
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 12px 16px;
  color: white;
  font-size: 0.9rem;
  outline: none;
  transition: all 0.3s ease;
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
  
  &:focus {
    border-color: rgba(102, 126, 234, 0.5);
    background: rgba(255, 255, 255, 0.15);
  }
`;

const SendButton = styled(motion.button)`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 10px;
  padding: 12px;
  cursor: pointer;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const QuickActions = styled.div`
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
`;

const QuickActionButton = styled(motion.button)`
  background: rgba(102, 126, 234, 0.2);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 20px;
  padding: 8px 12px;
  font-size: 0.8rem;
  color: #90cdf4;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  
  &:hover {
    background: rgba(102, 126, 234, 0.3);
    transform: translateY(-1px);
  }
`;

const TypingIndicator = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
`;

const TypingDots = styled.div`
  display: flex;
  gap: 4px;
  
  span {
    width: 6px;
    height: 6px;
    background: rgba(102, 126, 234, 0.6);
    border-radius: 50%;
    animation: typing 1.4s ease-in-out infinite;
    
    &:nth-child(2) {
      animation-delay: 0.2s;
    }
    
    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
  
  @keyframes typing {
    0%, 60%, 100% {
      transform: translateY(0);
      opacity: 0.4;
    }
    30% {
      transform: translateY(-10px);
      opacity: 1;
    }
  }
`;

// Enhanced Message Component to handle enriched message rendering
const MessageComponent = ({ message, isUser, onSuggestionClick }) => {
  const renderMessageContent = (content) => {
    return renderSafe(content);
  };

  const renderSuggestions = (suggestions) => {
    if (!suggestions || suggestions.length === 0) return null;

    return (
      <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {suggestions.map((suggestion, index) => (
          <QuickActionButton
            key={index}
            onClick={() => onSuggestionClick(suggestion)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            style={{ 
              fontSize: '0.8rem',
              padding: '6px 12px',
              background: 'rgba(72, 187, 120, 0.2)',
              borderColor: 'rgba(72, 187, 120, 0.3)',
              color: '#68d391'
            }}
          >
            💡 {suggestion}
          </QuickActionButton>
        ))}
      </div>
    );
  };

  const renderContextualInfo = (message) => {
    if (!message.insights || message.isUser) return null;

    const insights = message.insights;
    const hasInsights = insights.memories_used > 0 || insights.health_alerts > 0;

    if (!hasInsights) return null;

    return (
      <div style={{ 
        marginTop: '8px', 
        fontSize: '0.7rem', 
        color: 'rgba(255, 255, 255, 0.4)',
        fontStyle: 'italic',
        display: 'flex',
        gap: '12px',
        alignItems: 'center'
      }}>
        {insights.memories_used > 0 && (
          <span>💭 {insights.memories_used} memories</span>
        )}
        {insights.health_alerts > 0 && (
          <span>🔔 {insights.health_alerts} alerts</span>
        )}
        {message.confidence && (
          <span>🎯 {Math.round(message.confidence * 100)}% confident</span>
        )}
      </div>
    );
  };

  return (
    <Message
      isUser={isUser}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <MessageAvatar isUser={isUser}>
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </MessageAvatar>
      <div style={{ maxWidth: '70%' }}>
        <MessageBubble 
          isUser={isUser}
          style={{
            borderColor: message.isError 
              ? 'rgba(245, 101, 101, 0.3)' 
              : message.responseType === 'personalized'
              ? 'rgba(72, 187, 120, 0.3)'
              : undefined
          }}
        >
          {renderMessageContent(message.text)}
          {renderContextualInfo(message)}
        </MessageBubble>
        {message.isSuggestionList && renderSuggestions(message.suggestions)}
      </div>
    </Message>
  );
};

const AIHealthCoach = () => {
  const formatMessageText = (text) => {
    return renderSafe(text);
  };

  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const messagesEndRef = useRef(null);
  const { user, connectionStatus, BASE_URL, showToast } = useApp();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      // Concise, friendly welcome message
      const userName = user?.username || user?.name || "there";
      let welcomeText = `Hi ${userName}! 👋 I'm your AI Health Coach.\n\n`;
      
      if (user?.id) {
        welcomeText += `I remember our conversations and have access to your health insights. Ready to help you make healthier choices! 🌟\n\n`;
        welcomeText += `What's on your mind today?`;
      } else {
        welcomeText += `Please login to get personalized health coaching with memory and insights! 🔐`;
      }

      const welcomeMessage = {
        id: 1,
        text: welcomeText,
        isUser: false,
        timestamp: new Date(),
        responseType: 'welcome'
      };
      setMessages([welcomeMessage]);
    }
  }, [isOpen, messages.length, user]);

  const sendMessage = async (messageText = inputValue) => {
    if (!messageText.trim()) return;

    if (connectionStatus === 'offline') {
      showToast("This feature requires an internet connection", 'error');
      return;
    }

    // Check if user is logged in for personalized features
    if (!user?.id) {
      showToast("Please login for personalized AI health coaching", 'warning');
      return;
    }

    const userMessage = {
      id: Date.now(),
      text: messageText,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Build context with request for concise responses
      const enhancedContext = {
        user_id: user.id,
        chat_history: chatHistory.slice(-3), // Reduced to last 3 for more focused context
        current_session: `health_coach_${Date.now()}`,
        interaction_type: 'health_coaching',
        user_profile: user.profile || {},
        request_timestamp: new Date().toISOString(),
        preferences: {
          response_style: 'concise_friendly', // New preference for concise responses
          max_response_length: 'medium', // Request medium-length responses
          include_context_hints: true
        }
      };

      // Use enhanced agentic chat with optimized context
      const response = await fetch(`${BASE_URL}/agentic/chat/${user.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: messageText,
          session_id: enhancedContext.current_session,
          context: enhancedContext
        })
      });

      if (!response.ok) {
        throw new Error(`Enhanced chat failed: ${response.status}`);
      }

      const data = await response.json();

      // Process the enhanced AI response with improved formatting
      const responseText = formatMessageText(data.message || "I'm here to help with your health questions! 😊");

      // Create enhanced bot message with streamlined information
      const botMessage = {
        id: Date.now() + 1,
        text: responseText,
        isUser: false,
        timestamp: new Date(),
        responseType: data.response_type || 'general',
        suggestions: data.suggested_actions || [],
        insights: data.contextual_insights || {},
        proactiveFeatures: data.proactive_features || {},
        confidence: data.confidence || 0.8,
        sessionId: data.session_id
      };

      setMessages(prev => [...prev, botMessage]);

      // Handle urgent alerts with more user-friendly notifications
      if (data.urgent_alerts && data.urgent_alerts.length > 0) {
        showToast(`⚠️ ${data.urgent_alerts[0].message}`, 'warning');
      }

      // Show proactive insights (only the most important ones)
      if (data.proactive_features) {
        const features = data.proactive_features;
        
        // Prioritize most important notifications
        if (features.health_insights > 0) {
          showToast(`� New health insights available!`, 'info');
        } else if (features.meal_plan_suggested) {
          showToast("🍽️ Meal plan suggestion ready!", 'success');
        } else if (features.notifications_generated > 0) {
          showToast(`� Personalized tips generated!`, 'info');
        }
      }

      // Update chat history with streamlined data
      setChatHistory(prev => {
        const newHistory = [...prev, {
          user: messageText,
          agent: data.message,
          session_id: data.session_id,
          timestamp: new Date().toISOString()
        }];
        return newHistory.slice(-8); // Keep only last 8 exchanges for faster processing
      });

      // Show suggested actions as quick reply buttons (only if there are meaningful suggestions)
      if (data.suggested_actions && data.suggested_actions.length > 0 && data.suggested_actions.length <= 3) {
        setTimeout(() => {
          const suggestionMessage = {
            id: Date.now() + 2,
            text: "💡 Quick suggestions:",
            isUser: false,
            timestamp: new Date(),
            suggestions: data.suggested_actions.slice(0, 3), // Limit to 3 suggestions
            isSuggestionList: true
          };
          setMessages(prev => [...prev, suggestionMessage]);
        }, 800);
      }

    } catch (error) {
      console.error("Enhanced chat error:", error);
      
      // Provide concise, friendly error messages
      let errorText = "Oops! I'm having trouble right now. ";
      
      if (error.message.includes('404')) {
        errorText += "Please make sure you're logged in 🔐";
      } else if (error.message.includes('500')) {
        errorText += "Give me a moment to reconnect 🔄";
      } else {
        errorText += "Check your connection and try again 📶";
      }

      const errorMessage = {
        id: Date.now() + 1,
        text: errorText,
        isUser: false,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const getDailyTip = async () => {
    if (connectionStatus === 'offline') {
      showToast("Need internet connection 📶", 'error');
      return;
    }

    if (!user?.id) {
      showToast("Please login for personalized tips 🔐", 'warning');
      return;
    }

    try {
      // Request a brief, actionable daily tip
      await sendMessage("Give me a quick, actionable health tip for today");
    } catch (error) {
      console.error("Daily tip error:", error);
      showToast("Couldn't get your tip right now 😔", 'error');
    }
  };

  const getHealthDashboard = async () => {
    if (connectionStatus === 'offline') {
      showToast("Need internet connection 📶", 'error');
      return;
    }

    if (!user?.id) {
      showToast("Please login to view dashboard 🔐", 'warning');
      return;
    }

    try {
      // Use the enhanced chat for a concise dashboard summary
      await sendMessage("Show me a quick summary of my health dashboard and current status");
    } catch (error) {
      console.error("Dashboard error:", error);
      const errorMessage = {
        id: Date.now(),
        text: "Can't access your dashboard right now 📊 Try again in a moment!",
        isUser: false,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const getSmartNotifications = async () => {
    if (!user?.id) {
      showToast("Please login for notifications 🔐", 'warning');
      return;
    }

    try {
      // Use enhanced chat for smart notifications
      await sendMessage("Generate some smart notifications and reminders based on my health patterns");
    } catch (error) {
      console.error("Smart notifications error:", error);
      showToast("Couldn't generate notifications 🔔", 'error');
    }
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickActions = [
    { text: "Daily Tip", action: getDailyTip, icon: <Lightbulb size={14} /> },
    { text: "My Dashboard", action: getHealthDashboard, icon: <Bot size={14} /> },
    { text: "Smart Alerts", action: getSmartNotifications, icon: <MessageCircle size={14} /> },
    { text: "Meal Plan", action: () => sendMessage("Create a quick meal plan for me") },
    { text: "My Patterns", action: () => sendMessage("What patterns do you see in my eating habits?") },
    { text: "Goal Check", action: () => sendMessage("How am I doing with my health goals?") }
  ];

  return (
    <ChatBotContainer>
      <AnimatePresence>
        {isOpen && (
          <ChatWindow
            minimized={isMinimized}
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            transition={{ duration: 0.3 }}
          >
            <ChatHeader>
              <ChatHeaderLeft>
                <MessageAvatar isUser={false}>
                  <Bot size={18} />
                </MessageAvatar>
                <ChatHeaderTitle>
                  <ChatTitle>AI Health Coach</ChatTitle>
                  <ChatSubtitle>Always here to help</ChatSubtitle>
                </ChatHeaderTitle>
              </ChatHeaderLeft>
              <ChatHeaderButtons>
                <HeaderButton onClick={() => setIsMinimized(!isMinimized)}>
                  {isMinimized ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
                </HeaderButton>
                <HeaderButton onClick={() => setIsOpen(false)}>
                  <X size={16} />
                </HeaderButton>
              </ChatHeaderButtons>
            </ChatHeader>

            {!isMinimized && (
              <>
                <ChatMessages>
                  <QuickActions>
                    {quickActions.map((action, index) => (
                      <QuickActionButton
                        key={index}
                        onClick={action.action}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        {action.icon}
                        {action.text}
                      </QuickActionButton>
                    ))}
                  </QuickActions>

                  {messages.map((message) => (
                    <MessageComponent
                      key={message.id}
                      message={message}
                      isUser={message.isUser}
                      onSuggestionClick={handleSuggestionClick}
                    />
                  ))}

                  {isTyping && (
                    <TypingIndicator
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      <MessageAvatar isUser={false}>
                        <Bot size={16} />
                      </MessageAvatar>
                      <TypingDots>
                        <span></span>
                        <span></span>
                        <span></span>
                      </TypingDots>
                    </TypingIndicator>
                  )}

                  <div ref={messagesEndRef} />
                </ChatMessages>

                <ChatInput>
                  <InputField
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask your health coach anything..."
                    disabled={isTyping}
                  />
                  <SendButton
                    onClick={() => sendMessage()}
                    disabled={!inputValue.trim() || isTyping}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Send size={16} />
                  </SendButton>
                </ChatInput>
              </>
            )}
          </ChatWindow>
        )}
      </AnimatePresence>

      <ChatBotButton
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        animate={isOpen ? {} : { scale: [1, 1.05, 1] }}
        transition={isOpen ? {} : { duration: 2, repeat: Infinity }}
      >
        <AnimatePresence mode="wait">
          {isOpen ? (
            <motion.div
              key="close"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <X size={24} />
            </motion.div>
          ) : (
            <motion.div
              key="open"
              initial={{ rotate: 90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: -90, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <MessageCircle size={24} />
            </motion.div>
          )}
        </AnimatePresence>

        {!isOpen && (
          <PulseRing
            animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        )}
      </ChatBotButton>
    </ChatBotContainer>
  );
};

export default AIHealthCoach;
