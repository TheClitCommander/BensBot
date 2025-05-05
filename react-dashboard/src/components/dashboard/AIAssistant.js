import React, { useState } from 'react';

const AIAssistant = () => {
  const [userInput, setUserInput] = useState('');
  
  // Mock conversation history - would be connected to your AI coordinator
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      content: 'Good afternoon, Ben. Your portfolio is showing strong performance today with tech stocks leading the gains. How can I assist you with your trading today?',
      timestamp: new Date().toISOString()
    }
  ]);

  // Function to handle sending new messages
  const handleSendMessage = (e) => {
    e.preventDefault();
    
    if (!userInput.trim()) return;
    
    // Add user message
    const newMessages = [
      ...messages,
      {
        sender: 'user',
        content: userInput,
        timestamp: new Date().toISOString()
      }
    ];
    
    setMessages(newMessages);
    setUserInput('');
    
    // Simulate AI response (would connect to Minerva in production)
    setTimeout(() => {
      let aiResponse;
      
      // Simple logic to generate contextual responses
      if (userInput.toLowerCase().includes('portfolio')) {
        aiResponse = "Your portfolio is up 1.49% today. Your tech positions (AAPL, MSFT, GOOGL) are performing particularly well, contributing to most of today's gains. Would you like me to provide a detailed breakdown?";
      } else if (userInput.toLowerCase().includes('market')) {
        aiResponse = "The market is currently bullish with the S&P 500 up 0.8% and Nasdaq up 1.2%. Tech and healthcare sectors are leading gains while energy stocks are showing weakness due to declining oil prices.";
      } else if (userInput.toLowerCase().includes('recommendation') || userInput.toLowerCase().includes('suggest')) {
        aiResponse = "Based on current market conditions and your portfolio allocation, I suggest considering increasing your position in semiconductor stocks. Companies like NVDA and AMD are showing strong momentum with the AI boom continuing to drive demand.";
      } else {
        aiResponse = "I've analyzed your question and reviewed the latest market data. Let me provide you with insights tailored to your trading strategy. What specific aspect would you like me to elaborate on?";
      }
      
      setMessages([
        ...newMessages,
        {
          sender: 'ai',
          content: aiResponse,
          timestamp: new Date().toISOString()
        }
      ]);
    }, 1000);
  };

  return (
    <div className="card">
      <h2 className="card-header">Minerva AI Assistant</h2>
      <div className="card-content">
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '15px', 
          maxHeight: '300px', 
          overflowY: 'auto',
          padding: '0 5px',
          marginBottom: '15px'
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
              <div style={{ marginBottom: '5px', fontSize: '0.875rem' }}>
                {message.content}
              </div>
              <div style={{ fontSize: '0.7rem', opacity: 0.7, textAlign: 'right' }}>
                {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          ))}
        </div>
        
        <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Ask about market conditions, portfolio suggestions, or trading ideas..."
            style={{
              flex: 1,
              padding: '10px 15px',
              borderRadius: '5px',
              border: 'none',
              backgroundColor: '#333',
              color: '#e0e0e0'
            }}
          />
          <button
            type="submit"
            style={{
              padding: '10px 15px',
              borderRadius: '5px',
              border: 'none',
              backgroundColor: '#4F8BFF',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            <span className="material-icons" style={{ fontSize: '20px' }}>send</span>
          </button>
        </form>
        
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '15px' }}>
          <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap', justifyContent: 'center' }}>
            {['Market overview', 'Portfolio analysis', 'Trade suggestions', 'Risk assessment'].map((suggestion, index) => (
              <div
                key={index}
                onClick={() => setUserInput(suggestion)}
                style={{
                  padding: '5px 10px',
                  borderRadius: '15px',
                  backgroundColor: '#333',
                  color: '#e0e0e0',
                  fontSize: '0.875rem',
                  cursor: 'pointer'
                }}
              >
                {suggestion}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;
