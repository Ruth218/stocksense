import logging
import json
import re
from datetime import datetime

# Load predefined chatbot responses from a JSON file
try:
    with open('chatbot_responses.json', 'r') as f:
        CHATBOT_RESPONSES = json.load(f)
except Exception as e:
    logging.error(f"Error loading chatbot responses: {e}")
    CHATBOT_RESPONSES = {
        "default": [
            "I'm sorry, I don't have information on that topic yet.",
            "I couldn't find a specific answer for your query. Please try asking about Indian stocks, mutual funds, or forex markets.",
            "I'm not sure about that. Could you try rephrasing your question?"
        ],
        "greetings": [
            "Hello! How can I help you with Indian stocks, mutual funds, or forex markets today?",
            "Hi there! Ask me anything about the Indian financial markets!",
            "Welcome! I'm here to assist with your financial queries about Indian markets."
        ],
        "stock_basics": [
            "Stocks represent ownership in a company. When you buy a share, you own a small piece of that business.",
            "The Indian stock market primarily operates through the BSE (Bombay Stock Exchange) and NSE (National Stock Exchange).",
            "To invest in stocks, you need to open a demat account with a registered broker."
        ],
        "mutual_fund_basics": [
            "Mutual funds pool money from many investors to purchase securities like stocks and bonds.",
            "There are different types of mutual funds: equity funds, debt funds, hybrid funds, and more.",
            "Mutual funds in India are regulated by SEBI (Securities and Exchange Board of India)."
        ],
        "forex_basics": [
            "Forex (foreign exchange) involves trading one currency for another.",
            "The Indian Rupee (INR) is the currency of India, and its exchange rate fluctuates against other currencies.",
            "Major currency pairs involving INR include USD/INR, EUR/INR, GBP/INR, and JPY/INR."
        ],
        "investment_strategies": [
            "Common investment strategies include value investing, growth investing, and dollar-cost averaging.",
            "Diversification across asset classes can help reduce risk in your investment portfolio.",
            "Long-term investing typically yields better results than short-term trading for most investors."
        ],
        "market_timing": [
            "Market timing is difficult even for professional investors. A consistent investment approach often works better.",
            "Rather than trying to time the market, consider regular investments through SIPs (Systematic Investment Plans).",
            "Historical data shows that staying invested for the long term generally produces better returns than frequent trading."
        ],
        "tax": [
            "Short-term capital gains on equity investments (held for less than 1 year) are taxed at 15% in India.",
            "Long-term capital gains on equity exceeding ₹1 lakh are taxed at 10% without indexation benefit.",
            "Dividends from Indian companies are taxable in the hands of the recipient at their applicable income tax slab rate."
        ]
    }

def get_chatbot_response(query):
    """
    Generate a response based on the user query
    """
    query = query.lower().strip()
    
    # Check for greetings
    greetings = ["hi", "hello", "hey", "greetings", "namaste"]
    if any(greeting in query for greeting in greetings):
        return get_random_response("greetings")
    
    # Check for key topics
    if re.search(r'\b(stock|share|equity|nse|bse|sensex|nifty)\b', query):
        if "basics" in query or "what is" in query or "how to" in query:
            return get_random_response("stock_basics")
        
    if re.search(r'\b(mutual fund|mf|sip|elss|debt fund|equity fund)\b', query):
        if "basics" in query or "what is" in query or "how to" in query:
            return get_random_response("mutual_fund_basics")
    
    if re.search(r'\b(forex|currency|exchange rate|dollar|usd|foreign exchange|inr)\b', query):
        if "basics" in query or "what is" in query or "how to" in query:
            return get_random_response("forex_basics")
    
    if re.search(r'\b(strategy|invest|portfolio|diversify|allocation|asset)\b', query):
        return get_random_response("investment_strategies")
    
    if re.search(r'\b(timing|when|best time|market crash|correction|bull|bear)\b', query):
        return get_random_response("market_timing")
    
    if re.search(r'\b(tax|taxation|capital gain|dividend|stcg|ltcg)\b', query):
        return get_random_response("tax")
    
    # Default response if no pattern is matched
    return get_random_response("default")

def get_random_response(category):
    """
    Get a random response from the specified category
    """
    import random
    responses = CHATBOT_RESPONSES.get(category, CHATBOT_RESPONSES["default"])
    return random.choice(responses)

def save_chat_history(user_id, query, response):
    """
    Save chat history to a file or database
    """
    try:
        chat_entry = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response
        }
        
        # For simplicity, we'll append to a file
        with open("chat_history.json", "a") as f:
            f.write(json.dumps(chat_entry) + "\n")
            
        return True
    except Exception as e:
        logging.error(f"Error saving chat history: {e}")
        return False

def get_user_chat_history(user_id, limit=10):
    """
    Retrieve chat history for a specific user
    """
    try:
        history = []
        with open("chat_history.json", "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry["user_id"] == user_id:
                        history.append(entry)
                except json.JSONDecodeError:
                    continue
        
        # Return most recent conversations first
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)[:limit]
    except FileNotFoundError:
        return []
    except Exception as e:
        logging.error(f"Error retrieving chat history: {e}")
        return []