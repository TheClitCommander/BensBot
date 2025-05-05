import React, { useState, useEffect, FormEvent } from 'react';
import { aiApi } from '../../services/api';
import { getOpenAIResponse, resetConversation, setConversationHistory } from '../../services/openaiService';

interface Message {
  sender: 'user' | 'ai';
  content: string;
  timestamp: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  lastUpdatedAt: string;
}

const AIAssistant: React.FC = () => {
  const [userInput, setUserInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showHistory, setShowHistory] = useState<boolean>(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string>('');
  
  // Initialize with a welcome message
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'ai',
      content: 'Good afternoon, Ben. Your portfolio is showing strong performance today with tech stocks leading the gains. How can I assist you with your trading today?',
      timestamp: new Date().toISOString()
    }
  ]);
  
  // Generate a unique ID
  const generateId = (): string => {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
  };
  
  // Create a new conversation
  const createNewConversation = () => {
    const welcomeMessage: Message = {
      sender: 'ai',
      content: 'Good afternoon, Ben. Your portfolio is showing strong performance today with tech stocks leading the gains. How can I assist you with your trading today?',
      timestamp: new Date().toISOString()
    };
    
    const newConversation: Conversation = {
      id: generateId(),
      title: 'New Conversation',
      messages: [welcomeMessage],
      createdAt: new Date().toISOString(),
      lastUpdatedAt: new Date().toISOString()
    };
    
    const updatedConversations = [...conversations, newConversation];
    setConversations(updatedConversations);
    setMessages(newConversation.messages);
    setActiveConversationId(newConversation.id);
    
    // Reset OpenAI conversation history
    resetConversation();
    setConversationHistory([welcomeMessage]);
    
    // Save to localStorage
    localStorage.setItem('aiAssistantConversations', JSON.stringify(updatedConversations));
  };
  
  // Load conversations from localStorage
  useEffect(() => {
    const savedConversations = localStorage.getItem('aiAssistantConversations');
    if (savedConversations) {
      const parsedConversations: Conversation[] = JSON.parse(savedConversations);
      setConversations(parsedConversations);
      
      // If there are conversations, load the most recent one
      if (parsedConversations.length > 0) {
        const mostRecent = parsedConversations.sort((a, b) => 
          new Date(b.lastUpdatedAt).getTime() - new Date(a.lastUpdatedAt).getTime())[0];
        setMessages(mostRecent.messages);
        setActiveConversationId(mostRecent.id);
      } else {
        // If no saved conversations, create a new one
        createNewConversation();
      }
    } else {
      // If no saved conversations, create a new one
      createNewConversation();
    }
  }, []);
  
  // Update conversation title based on first user message
  const updateConversationTitle = (userMessage: string) => {
    if (!activeConversationId) return;
    
    const activeConversation = conversations.find(c => c.id === activeConversationId);
    if (!activeConversation) return;
    
    // Only update title if it's still the default 'New Conversation'
    if (activeConversation.title === 'New Conversation') {
      // Use the first ~20 chars of user message as the title
      const newTitle = userMessage.length > 20 
        ? userMessage.substring(0, 20) + '...' 
        : userMessage;
      
      const updatedConversations = conversations.map(c => 
        c.id === activeConversationId 
          ? { ...c, title: newTitle } 
          : c
      );
      
      setConversations(updatedConversations);
      
      // Save to localStorage
      localStorage.setItem('aiAssistantConversations', JSON.stringify(updatedConversations));
    }
  };

  // This function is now just a fallback - the main responses come from the API service
  // which has its own fallback mechanism with contextual responses
  const getResponse = (input: string): string => {
    return "I'm currently using fallback mode as I can't connect to the AI backend. Please try again later.";
  };
  
  // Save messages to the active conversation
  const saveMessagesToConversation = (updatedMessages: Message[]) => {
    if (!activeConversationId) return;
    
    const updatedConversations = conversations.map(c => 
      c.id === activeConversationId 
        ? { 
            ...c, 
            messages: updatedMessages,
            lastUpdatedAt: new Date().toISOString()
          } 
        : c
    );
    
    setConversations(updatedConversations);
    
    // Save to localStorage
    localStorage.setItem('aiAssistantConversations', JSON.stringify(updatedConversations));
  };
  
  // Load a conversation from history
  const loadConversation = (conversationId: string) => {
    const conversation = conversations.find(c => c.id === conversationId);
    if (conversation) {
      setMessages(conversation.messages);
      setActiveConversationId(conversationId);

      // Sync conversation history with OpenAI service
      setConversationHistory(conversation.messages);
    }
  };

  // Delete a conversation
  const deleteConversation = (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering the parent onClick

    const updatedConversations = conversations.filter(c => c.id !== conversationId);
    setConversations(updatedConversations);

    // If we're deleting the active conversation, switch to another one or create new
    if (conversationId === activeConversationId) {
      if (updatedConversations.length > 0) {
        const mostRecent = updatedConversations.sort((a, b) =>
          new Date(b.lastUpdatedAt).getTime() - new Date(a.lastUpdatedAt).getTime())[0];
        setMessages(mostRecent.messages);
        setActiveConversationId(mostRecent.id);
      } else {
        createNewConversation();
      }
    }

    // Save to localStorage
    localStorage.setItem('aiAssistantConversations', JSON.stringify(updatedConversations));
  };

  // Function to handle sending new messages
  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault();

    if (!userInput.trim() || isLoading) return;

    // If active conversation doesn't exist, create a new one
    if (!activeConversationId) {
      createNewConversation();
    }

    const userMessage: Message = {
      sender: 'user',
      content: userInput,
      timestamp: new Date().toISOString()
    };

    // Add user message to UI immediately
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    saveMessagesToConversation(updatedMessages);

    // Update conversation title if needed
    updateConversationTitle(userInput);

    // Store current input and clear the input field
    const currentInput = userInput;
    setUserInput('');
    setIsLoading(true);

    try {
      // First try direct OpenAI integration
      try {
        // Sync conversation history with OpenAI service
        setConversationHistory(updatedMessages);

        // Get response directly from OpenAI
        const aiResponse = await getOpenAIResponse(currentInput);

        const aiMessage: Message = {
          sender: 'ai',
          content: aiResponse,
          timestamp: new Date().toISOString()
        };

        // Add AI response to messages
        const messagesWithAI = [...updatedMessages, aiMessage];
        setMessages(messagesWithAI);
        saveMessagesToConversation(messagesWithAI);
        return; // Exit early if OpenAI call succeeded
      } catch (openaiError) {
        console.warn('OpenAI direct integration failed, falling back to API:', openaiError);
        // Continue to fallback if OpenAI direct integration fails
      }

      // Fallback to API
      const response = await aiApi.sendMessage(currentInput);

      const aiMessage: Message = {
        sender: 'ai',
        content: response.response || "I'm having trouble processing that request.",
        timestamp: new Date().toISOString()
      };

      // Add AI response to messages
      const messagesWithAI = [...updatedMessages, aiMessage];
      setMessages(messagesWithAI);
      saveMessagesToConversation(messagesWithAI);
    } catch (error) {
      console.error('Error getting AI response:', error);

      // Add error message
      const errorMessage: Message = {
        sender: 'ai',
        content: 'Sorry, I encountered an error. Please try again later.',
        timestamp: new Date().toISOString()
      };

      const messagesWithError = [...updatedMessages, errorMessage];
      setMessages(messagesWithError);
      saveMessagesToConversation(messagesWithError);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ 
      backgroundColor: '#1a1a1a', 
      borderRadius: '10px',
      padding: '20px',
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '15px',
        color: '#e0e0e0'
      }}>
        <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Trading AI Assistant</h2>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={() => setShowHistory(!showHistory)}
            style={{
              backgroundColor: '#333',
              color: '#e0e0e0',
              border: 'none',
              borderRadius: '5px',
              padding: '5px 10px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              fontSize: '0.875rem'
            }}
          >
            <span className="material-icons" style={{ fontSize: '16px' }}>
              {showHistory ? 'close' : 'history'}
            </span>
            {showHistory ? 'Close History' : 'History'}
          </button>
          <button 
            onClick={createNewConversation}
            style={{
              backgroundColor: '#4F8BFF',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              padding: '5px 10px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              fontSize: '0.875rem'
            }}
          >
            <span className="material-icons" style={{ fontSize: '16px' }}>add</span>
            New Chat
          </button>
        </div>
      </div>
      
      <div style={{ 
        display: 'flex',
        flexDirection: 'column',
        gap: '15px',
        height: '100%'
      }}>
        {/* Main Chat Area */}
        <div style={{ 
          display: 'flex',
          flexDirection: 'column',
          gap: '15px',
          height: '100%'
        }}>
          <div style={{ 
            flex: 1, 
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '15px',
            paddingRight: '5px',
            maxHeight: '350px' // Set a max height to prevent overflow
          }}>
            {messages.map((message, index) => (
              <div 
                key={index}
                style={{
                  alignSelf: message.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '80%',
                  padding: '10px 15px',
                  borderRadius: message.sender === 'user' ? '15px 15px 0 15px' : '15px 15px 15px 0',
                  backgroundColor: message.sender === 'user' ? '#4F8BFF' : '#333',
                  color: message.sender === 'user' ? 'white' : '#e0e0e0'
                }}
              >
                <div style={{ marginBottom: '5px', fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>
                  {message.content}
                </div>
                <div style={{ fontSize: '0.7rem', opacity: 0.7, textAlign: 'right' }}>
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div style={{ 
                alignSelf: 'flex-start',
                padding: '10px 15px',
                borderRadius: '15px 15px 15px 0',
                backgroundColor: '#333',
                color: '#e0e0e0',
                fontSize: '0.875rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <div style={{ display: 'flex', gap: '3px' }}>
                  <span style={{ 
                    display: 'inline-block', 
                    width: '8px', 
                    height: '8px', 
                    backgroundColor: '#4F8BFF',
                    borderRadius: '50%',
                    animation: 'pulse 1s infinite',
                    animationDelay: '0s'
                  }}></span>
                  <span style={{ 
                    display: 'inline-block', 
                    width: '8px', 
                    height: '8px', 
                    backgroundColor: '#4F8BFF',
                    borderRadius: '50%',
                    animation: 'pulse 1s infinite',
                    animationDelay: '0.2s'
                  }}></span>
                  <span style={{ 
                    display: 'inline-block', 
                    width: '8px', 
                    height: '8px', 
                    backgroundColor: '#4F8BFF',
                    borderRadius: '50%',
                    animation: 'pulse 1s infinite',
                    animationDelay: '0.4s'
                  }}></span>
                </div>
                <span>AI is thinking...</span>
              </div>
            )}
          </div>
          
          <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Ask about market conditions, portfolio suggestions, or trading ideas..."
              disabled={isLoading}
              style={{
                flex: 1,
                padding: '10px 15px',
                borderRadius: '5px',
                border: 'none',
                backgroundColor: '#333',
                color: '#e0e0e0',
                opacity: isLoading ? 0.7 : 1
              }}
            />
            <button
              type="submit"
              disabled={isLoading || !userInput.trim()}
              style={{
                padding: '10px 15px',
                borderRadius: '5px',
                border: 'none',
                backgroundColor: isLoading || !userInput.trim() ? '#666' : '#4F8BFF',
                color: 'white',
                cursor: isLoading || !userInput.trim() ? 'not-allowed' : 'pointer'
              }}
            >
              <span className="material-icons" style={{ fontSize: '20px' }}>
                {isLoading ? 'hourglass_empty' : 'send'}
              </span>
            </button>
          </form>
          
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '15px', marginBottom: '10px' }}>
            <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap', justifyContent: 'center' }}>
              {['Market overview', 'Portfolio analysis', 'Trade suggestions', 'Risk assessment'].map((suggestion, index) => (
                <div
                  key={index}
                  onClick={() => !isLoading && setUserInput(suggestion)}
                  style={{
                    padding: '5px 10px',
                    borderRadius: '15px',
                    backgroundColor: '#333',
                    color: '#e0e0e0',
                    fontSize: '0.875rem',
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    opacity: isLoading ? 0.7 : 1
                  }}
                >
                  {suggestion}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Conversation History Section */}
        {conversations.length > 1 && (
          <div style={{
            backgroundColor: '#222',
            borderRadius: '8px',
            padding: '15px',
            marginTop: '20px'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '10px'
            }}>
              <h3 style={{ margin: 0, fontSize: '1rem', color: '#e0e0e0' }}>Previous Conversations</h3>
              <button
                onClick={createNewConversation}
                style={{
                  backgroundColor: '#4F8BFF',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  padding: '5px 10px',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px'
                }}
              >
                <span className="material-icons" style={{ fontSize: '16px' }}>add</span>
                New Conversation
              </button>
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: '10px',
              maxHeight: '300px',
              overflowY: 'auto',
              padding: '5px'
            }}>
              {conversations
                .filter(c => c.id !== activeConversationId) // Don't show the active conversation
                .sort((a, b) => new Date(b.lastUpdatedAt).getTime() - new Date(a.lastUpdatedAt).getTime())
                .map(conversation => (
                  <div
                    key={conversation.id}
                    onClick={() => loadConversation(conversation.id)}
                    style={{
                      backgroundColor: '#2a2a2a',
                      borderRadius: '8px',
                      padding: '12px',
                      cursor: 'pointer',
                      border: '1px solid #333',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: '8px'
                    }}>
                      <div style={{
                        fontWeight: 'bold',
                        fontSize: '0.9rem',
                        color: '#e0e0e0',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {conversation.title}
                      </div>
                      <div style={{
                        display: 'flex',
                        gap: '5px'
                      }}>
                        <button
                          onClick={(e) => deleteConversation(conversation.id, e)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#999',
                            cursor: 'pointer',
                            padding: '2px',
                            borderRadius: '3px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                        >
                          <span className="material-icons" style={{ fontSize: '14px' }}>delete</span>
                        </button>
                      </div>
                    </div>
                    
                    <div style={{ fontSize: '0.8rem', color: '#999', marginBottom: '5px' }}>
                      {new Date(conversation.lastUpdatedAt).toLocaleString()}
                    </div>
                    
                    <div style={{ 
                      color: '#bbb',
                      fontSize: '0.85rem',
                      maxHeight: '60px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical'
                    }}>
                      {/* Show a snippet of the last message */}
                      {conversation.messages.length > 0 && 
                        conversation.messages[conversation.messages.length - 1].content}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIAssistant;
