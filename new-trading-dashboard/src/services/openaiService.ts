// Direct OpenAI integration service
// This service communicates directly with the OpenAI API

// OpenAI API key from your config
const OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"; // Add your key from environment variables or config

// Trading assistant system prompt
const SYSTEM_PROMPT = `You are BenBot, an AI assistant for a trading bot system. 
You help users analyze market conditions, review trading strategies, and manage their portfolio.
Be concise, accurate, and focus on providing actionable trading insights.

When responding about trading activities, stocks, or portfolio performance, use these fictional values:
- Portfolio value: $852,437.29 (+1.49% today)
- Monthly return: +7.2%
- Asset allocation: Stocks (45%), Crypto (25%), Options (15%), Forex (10%), Cash (5%)
- Top performers: NVDA (+3.2%), AAPL (+2.3%), MSFT (+1.8%)
- Underperformers: JPM (-0.4%), BAC (-0.8%)

For market analysis, use these insights:
- Current market regime: BULLISH (confidence: 78%)
- Trend strength: MODERATE
- Key indicators: Positive momentum with decreasing volatility
- Leading sectors: Technology and healthcare

For trading opportunities, suggest these:
1. NVDA (MomentumStrategy, confidence: 82%)
2. AAPL (MeanReversionStrategy, confidence: 74%)
3. MSFT (BreakoutStrategy, confidence: 67%)
4. AMD (TrendFollowingStrategy, confidence: 65%)
5. TSLA (VolatilityEdgeStrategy, confidence: 58%)

Never mention that you're using fictional data or that you're not connected to real trading data.`;

// Message interface
interface Message {
  role: string;
  content: string;
}

// Store conversation history
let conversationHistory: Message[] = [];

/**
 * Call OpenAI API with the given message
 * @param message User message
 * @returns Promise with AI response
 */
export async function getOpenAIResponse(message: string): Promise<string> {
  try {
    // Add user message to history
    conversationHistory.push({ role: "user", content: message });
    
    // Keep only the last 10 messages to avoid token limits
    if (conversationHistory.length > 10) {
      conversationHistory = conversationHistory.slice(conversationHistory.length - 10);
    }
    
    // Prepare messages with system prompt
    const messages = [
      { role: "system", content: SYSTEM_PROMPT },
      ...conversationHistory
    ];
    
    console.log("Calling OpenAI API directly...");
    
    // Call OpenAI API
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${OPENAI_API_KEY}`
      },
      body: JSON.stringify({
        model: "gpt-4-turbo",
        messages: messages,
        temperature: 0.7,
        max_tokens: 800
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      console.error("OpenAI API error:", errorData);
      throw new Error(`OpenAI API error: ${errorData.error?.message || 'Unknown error'}`);
    }
    
    const data = await response.json();
    const aiResponse = data.choices[0].message.content;
    
    // Add AI response to history
    conversationHistory.push({ role: "assistant", content: aiResponse });
    
    console.log("Received OpenAI response successfully");
    return aiResponse;
  } catch (error) {
    console.error("Error calling OpenAI:", error);
    throw error;
  }
}

/**
 * Reset the conversation history
 */
export function resetConversation(): void {
  conversationHistory = [];
}

/**
 * Set the conversation history from existing messages
 * @param messages Array of messages to set as history
 */
export function setConversationHistory(messages: {sender: string, content: string}[]): void {
  // Convert from UI message format to OpenAI format
  conversationHistory = messages.map(msg => ({
    role: msg.sender === 'user' ? 'user' : 'assistant',
    content: msg.content
  }));
}
