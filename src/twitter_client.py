# File Navigation Location: bahrain_airport_analyzer/src/main.py

import os
import pandas as pd
from dotenv import load_dotenv
from twitter_client import TwitterClient # Assuming twitter_client.py is in the same src directory
from gemini_analyzer import GeminiAnalyzer # Assuming gemini_analyzer.py is in the same src directory

# Load environment variables from .env.example or Codespaces secrets
load_dotenv()

# Configuration
# Ensure these defaults are 10 to comply with Twitter API min limits for max_results
# and to minimize API calls for testing.
TWITTER_SEARCH_QUERY = os.environ.get('TWITTER_QUERY', '@GulfAir -is:retweet') # Your desired query
MAX_MENTIONS_TO_FETCH = int(os.environ.get('MAX_MENTIONS_TO_FETCH', 10))
MAX_COMMENTS_PER_MENTION = int(os.environ.get('MAX_COMMENTS_PER_MENTION', 10))
OUTPUT_CSV_FILE = "data/bahrain_airport_comment_sentiments.csv" # Output file path

def run_analysis():
    print("Starting Twitter mention and sentiment analysis...")

    try:
        twitter = TwitterClient()
        gemini = GeminiAnalyzer()
    except ValueError as e:
        print(f"Error initializing clients: {e}")
        return
    except Exception as e: # Catch any other unexpected error during initialization
        print(f"An unexpected error occurred during client initialization: {e}")
        return

    # Ensure MAX_MENTIONS_TO_FETCH is at least 10 for the API call
    # The twitter_client.py now also has a safeguard for this.
    actual_max_mentions = max(10, MAX_MENTIONS_TO_FETCH) 
    
    print(f"Fetching up to {actual_max_mentions} mentions for query: {TWITTER_SEARCH_QUERY}")
    # This will be 1 API call to Twitter
    mentions = twitter.get_mentions(query=TWITTER_SEARCH_QUERY, max_results=actual_max_mentions)

    if not mentions:
        print("No mentions found. Exiting.")
        return

    all_analyzed_comments = []
    processed_one_mention_for_comments = False # Flag to ensure we only get comments for one mention

    print(f"\n--- Found {len(mentions)} mentions. Processing comments for the first valid one only. ---")

    for mention_index, mention in enumerate(mentions):
        # We will process all found mentions for their text, but only get comments for the first one.
        print(f"\nMention ({mention_index + 1}/{len(mentions)}): Tweet ID: {mention.id} | Text: {mention.text}")

        if not processed_one_mention_for_comments:
            if not mention.author_id:
                print(f"  Skipping comment retrieval for mention {mention.id} due to missing author_id.")
                # We might still want to process the next mention for comments if this one fails
                # Or, if you strictly want to try only the very first mention encountered:
                # processed_one_mention_for_comments = True # Mark as processed even if skipped
                continue # Try the next mention for comments if this one has no author_id

            # Ensure MAX_COMMENTS_PER_MENTION is at least 10 for the API call
            # The twitter_client.py now also has a safeguard for this.
            actual_max_comments = max(10, MAX_COMMENTS_PER_MENTION)

            print(f"  Attempting to fetch up to {actual_max_comments} comments for this mention (Tweet ID: {mention.id})...")
            # This will be 1 API call to Twitter (for this first processed mention)
            comments = twitter.get_comments_on_tweet(
                tweet_id=mention.id,
                conversation_id=mention.conversation_id,
                original_tweet_author_id=mention.author_id,
                max_results=actual_max_comments
            )

            if comments:
                print(f"    Found {len(comments)} comments for mention {mention.id}.")
                for comment_index, comment in enumerate(comments):
                    print(f"      Analyzing Comment ({comment_index + 1}/{len(comments)}) ID: {comment.id} | Text: {comment.text}")
                    sentiment = gemini.analyze_sentiment(comment.text)
                    print(f"      Sentiment: {sentiment}")
                    all_analyzed_comments.append({
                        "mention_tweet_id": mention.id,
                        "mention_tweet_text": mention.text,
                        "comment_id": comment.id,
                        "comment_text": comment.text,
                        "comment_author_id": comment.author_id,
                        "comment_created_at": comment.created_at,
                        "sentiment": sentiment
                    })
            else:
                print(f"    No comments found or retrieved for mention {mention.id}.")
            
            processed_one_mention_for_comments = True # Set the flag so we don't get comments for subsequent mentions
            # If you strictly only want to attempt comment retrieval for the VERY first mention,
            # and then stop processing further mentions entirely, you can add 'break' here.
            # For now, it will print info for other mentions but not fetch their comments.
            # To stop after the first mention entirely (no further mention printing):
            # break

    if all_analyzed_comments:
        # Ensure the 'data' directory exists
        data_dir = "data"
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
                print(f"Created directory: {data_dir}")
            except OSError as e:
                print(f"Error creating directory {data_dir}: {e}")
                # Fallback or decide how to handle if dir creation fails
        
        if os.path.exists(data_dir):
            df = pd.DataFrame(all_analyzed_comments)
            try:
                df.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8')
                print(f"\nAnalysis complete. Results for comments saved to {OUTPUT_CSV_FILE}")
                print("First few rows of the saved data:")
                print(df.head())
            except IOError as e:
                print(f"Error saving results to CSV {OUTPUT_CSV_FILE}: {e}")
                print("\nDisplaying results in console instead:")
                print(df)
        else:
            print(f"Could not create or find data directory '{data_dir}'. Results not saved to CSV.")
            if all_analyzed_comments:
                 df = pd.DataFrame(all_analyzed_comments)
                 print("\nDisplaying results in console:")
                 print(df)

    else:
        print("\nNo comments were analyzed or no mentions led to comment analysis.")

if __name__ == "__main__":
    run_analysis()