import os
import pandas as pd
from dotenv import load_dotenv
from twitter_client import TwitterClient
from gemini_analyzer import GeminiAnalyzer

# Load environment variables from .env.example or Codespaces secrets
load_dotenv()

# Configuration (can be moved to a config file or set via environment variables)
# Get from .env.example or set directly if not in env
TWITTER_SEARCH_QUERY = os.environ.get('TWITTER_QUERY', '@GulfAir -is:retweet')
MAX_MENTIONS_TO_FETCH = int(os.environ.get('MAX_MENTIONS_TO_FETCH', 5)) # Be mindful of API limits
MAX_COMMENTS_PER_MENTION = int(os.environ.get('MAX_COMMENTS_PER_MENTION', 10)) # Be mindful of API limits
OUTPUT_CSV_FILE = "data/bahrain_airport_comment_sentiments.csv"

def run_analysis():
    print("Starting Twitter mention and sentiment analysis...")

    try:
        twitter = TwitterClient()
        gemini = GeminiAnalyzer()
    except ValueError as e:
        print(f"Error initializing clients: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred during initialization: {e}")
        return

    print(f"Fetching up to {MAX_MENTIONS_TO_FETCH} mentions for query: {TWITTER_SEARCH_QUERY}")
    mentions = twitter.get_mentions(query=TWITTER_SEARCH_QUERY, max_results=MAX_MENTIONS_TO_FETCH)

    if not mentions:
        print("No mentions found. Exiting.")
        return

    all_analyzed_comments = []

    for mention in mentions:
        print(f"\nProcessing Mention Tweet ID: {mention.id} | Text: {mention.text}")
        # The author_id of the tweet that contains the mention is mention.author_id
        comments = twitter.get_comments_on_tweet(
            tweet_id=mention.id,
            conversation_id=mention.conversation_id,
            original_tweet_author_id=mention.author_id,
            max_results=MAX_COMMENTS_PER_MENTION
        )

        if comments:
            for comment in comments:
                print(f"  Analyzing Comment ID: {comment.id} | Text: {comment.text}")
                sentiment = gemini.analyze_sentiment(comment.text)
                print(f"  Sentiment: {sentiment}")
                all_analyzed_comments.append({
                    "mention_tweet_id": mention.id,
                    "mention_tweet_text": mention.text,
                    "comment_id": comment.id,
                    "comment_text": comment.text,
                    "comment_author_id": comment.author_id,
                    # "comment_author_username": comment.author.username if comment.author else "N/A", # Requires correct expansion and data access
                    "comment_created_at": comment.created_at,
                    "sentiment": sentiment
                })
        else:
            print(f"  No comments found or retrieved for mention {mention.id}.")

    if all_analyzed_comments:
        # Ensure the 'data' directory exists
        if not os.path.exists("data"):
            os.makedirs("data")

        df = pd.DataFrame(all_analyzed_comments)
        try:
            df.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8')
            print(f"\nAnalysis complete. Results saved to {OUTPUT_CSV_FILE}")
            print(df.head())
        except IOError as e:
            print(f"Error saving results to CSV: {e}")
            print("\nDisplaying results in console instead:")
            print(df)
    else:
        print("\nNo comments were analyzed.")

if __name__ == "__main__":
    run_analysis()