import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables.")
    # Raise an exception or handle as appropriate
else:
    genai.configure(api_key=GEMINI_API_KEY)

class GeminiAnalyzer:
    def __init__(self, model_name='gemini-pro'):
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API Key not configured.")
        try:
            self.model = genai.GenerativeModel(model_name)
            # Test generation to ensure API key is valid and model is accessible
            # self.model.generate_content("test") # Optional: can do a quick test
            print(f"Gemini model '{model_name}' initialized successfully.")
        except Exception as e:
            print(f"Error initializing Gemini model '{model_name}': {e}")
            raise

    def analyze_sentiment(self, text_content):
        """
        Analyzes the sentiment of a given text using the Gemini API.
        Returns 'positive', 'negative', or 'neutral'.
        """
        if not self.model:
            print("Gemini model not initialized.")
            return "error"

        prompt = f"""Analyze the sentiment of the following text.
Classify it as 'positive', 'negative', or 'neutral'.
Return only one of these three words.

Text: "{text_content}"
Sentiment:"""

        try:
            response = self.model.generate_content(prompt)
            sentiment = response.text.strip().lower()

            # More robust checking for the specific keywords
            if 'positive' in sentiment and 'negative' not in sentiment: # handles cases like "positive sentiment"
                return 'positive'
            elif 'negative' in sentiment and 'positive' not in sentiment: # handles "negative sentiment"
                return 'negative'
            elif 'neutral' in sentiment: # handles "neutral sentiment"
                return 'neutral'
            else:
                # If the response is exactly one of the words (less likely with complex models but good to check)
                if sentiment in ['positive', 'negative', 'neutral']:
                    return sentiment
                print(f"Warning: Unexpected sentiment output '{response.text}'. Could not reliably classify. Defaulting to neutral.")
                # You could inspect response.candidates or response.prompt_feedback for more details
                # print(f"Prompt feedback: {response.prompt_feedback}")
                return "neutral" # Default or further error handling

        except Exception as e:
            print(f"Error during sentiment analysis with Gemini: {e}")
            # if hasattr(e, 'response') and hasattr(e.response, 'prompt_feedback'):
            #     print(f"Prompt feedback: {e.response.prompt_feedback}")
            return "error"

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    # Ensure GEMINI_API_KEY is set in your environment or .env file
    try:
        analyzer = GeminiAnalyzer()
        test_texts = [
            "I love Bahrain Airport! The service is amazing.",
            "The flight was delayed and the staff were unhelpful at Bahrain Airport.",
            "My experience at Bahrain Airport was okay, nothing special.",
            "The new terminal at Bahrain International Airport looks fantastic and is very efficient.",
            "I'm frustrated with the parking situation at the airport in Bahrain."
        ]
        for text in test_texts:
            sentiment = analyzer.analyze_sentiment(text)
            print(f"Text: \"{text}\" \nSentiment: {sentiment}\n---")

        # Test with potentially problematic output from model (if it doesn't just give one word)
        # Mocking a more verbose response for testing the parsing:
        class MockResponse:
            def __init__(self, text):
                self.text = text
        analyzer.model.generate_content = lambda prompt: MockResponse("The sentiment of the text is clearly positive.")
        print("Testing with verbose positive mock response:")
        sentiment = analyzer.analyze_sentiment("This is a test.")
        print(f"Text: \"This is a test.\" \nSentiment: {sentiment}\n---")


    except ValueError as ve:
        print(f"Setup Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}")