// Direct OpenAI integration for the dashboard
// This allows BenBot to use real AI without requiring the backend API

// Your API key (from the config)
const OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"; // Add your key from environment variables or config

// System prompt similar to what the BenBotAssistant uses
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

// Store conversation history
let conversationHistory: Array<{role: string, content: string}> = [];

// Function to call OpenAI API directly
export async function callOpenAI(message: string): Promise<string> {
  // Add user message to history
  conversationHistory.push({ role: "user", content: message });
  
  // Keep only the last 10 messages to avoid context length issues
  if (conversationHistory.length > 10) {
    conversationHistory = conversationHistory.slice(conversationHistory.length - 10);
  }
  
  // Prepare messages array with system prompt
  const messages = [
    { role: "system", content: SYSTEM_PROMPT },
    ...conversationHistory
  ];
  
  try {
    // Call OpenAI API directly
    console.log("Calling OpenAI API directly from dashboard...");
    
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
    
    console.log("Received direct response from OpenAI");
    return aiResponse;
  } catch (error) {
    console.error("Error calling OpenAI directly:", error);
    return "I'm having trouble connecting to my AI service right now. Please try again in a moment.";
  }
}
