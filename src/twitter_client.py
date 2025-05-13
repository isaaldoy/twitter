import tweepy
import os
from dotenv import load_dotenv # For loading .env file if not using Codespaces secrets directly

# Load environment variables if an .env file is present (for local dev)
load_dotenv()

# It's best practice to get secrets from environment variables,
# which GitHub Codespaces populates from its secrets store.
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

if not TWITTER_BEARER_TOKEN:
    print("Error: TWITTER_BEARER_TOKEN not found in environment variables.")
    # You might want to raise an exception here or handle it more gracefully
    # For now, we'll let it proceed and tweepy will likely fail if it's None

class TwitterClient:
    def __init__(self):
        if not TWITTER_BEARER_TOKEN:
            raise ValueError("Twitter Bearer Token not configured.")
        self.client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

    def get_mentions(self, query, max_results=10):
        """
        Fetches recent tweets mentioning the specified query.
        """
        if not self.client:
            print("Twitter client not initialized.")
            return []
        try:
            print(f"Searching for mentions with query: {query}")
            response = self.client.search_recent_tweets(
                query=query,
                tweet_fields=['id', 'text', 'created_at', 'author_id', 'conversation_id', 'in_reply_to_user_id'],
                expansions=['author_id'], # To get user details like username
                user_fields=['username'],
                max_results=max_results
            )
            # print(f"Twitter API Response: {response}") # For debugging

            mentioning_tweets = response.data
            if not mentioning_tweets:
                print("No recent mentions found.")
                return []
            return mentioning_tweets
        except tweepy.TweepyException as e:
            print(f"Error searching tweets: {e}")
            if response and response.errors:
                print(f"API Errors: {response.errors}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred while fetching mentions: {e}")
            return []

    def get_comments_on_tweet(self, tweet_id, conversation_id, original_tweet_author_id, company_twitter_id=None, max_results=20):
        """
        Fetches replies (comments) to a specific tweet, trying to focus on relevant replies.
        `original_tweet_author_id` is the author of the tweet that contained the mention.
        `company_twitter_id` (string) is the user ID of the company account, if you want to filter replies
        specifically to the company if the company itself made the original tweet.
        """
        if not self.client:
            print("Twitter client not initialized.")
            return []
        try:
            # Query for replies within the same conversation, not by the original tweet author
            # and ensuring they are replies (have 'in_reply_to_user_id')
            # Note: `is:reply` doesn't always work as expected in standard search for recent tweets.
            # Focusing on conversation_id and ensuring in_reply_to_user_id is present is more robust.
            reply_query = f"conversation_id:{conversation_id} -from:{original_tweet_author_id}"

            # If the original tweet was by the company, you might only want replies to that specific tweet.
            # If the mention was by someone else, you want replies to *their* tweet.
            # A more precise way to get direct replies to `tweet_id`:
            # reply_query = f"in_reply_to_tweet_id:{tweet_id} -is:retweet"
            # However, `in_reply_to_tweet_id` is a v1.1 operator primarily.
            # For v2, `conversation_id` is key. We then filter.

            print(f"Searching for comments with query: {reply_query} for tweet_id: {tweet_id}")

            response = self.client.search_recent_tweets(
                query=reply_query,
                tweet_fields=['id', 'text', 'created_at', 'author_id', 'in_reply_to_user_id', 'conversation_id'],
                expansions=['author_id'],
                user_fields=['username'],
                max_results=max_results
            )
            # print(f"Twitter API Response (Comments): {response}") # For debugging

            all_replies_in_conversation = response.data
            comments_on_specific_tweet = []

            if all_replies_in_conversation:
                for reply in all_replies_in_conversation:
                    # This is a crucial filtering step:
                    # We want replies *to the tweet that contained the mention* (tweet_id)
                    # or, if the mention *is* the original tweet of the conversation,
                    # any reply in that conversation (excluding replies to other replies further down the chain, if desired).
                    # For simplicity here, we're taking replies within the conversation.
                    # A more robust check would be `if reply.in_reply_to_user_id == original_tweet_author_id`
                    # AND potentially `reply.referenced_tweets` contains a reference to `tweet_id`
                    # However, `referenced_tweets` might not be directly available in `tweet_fields` for search.
                    # We need to check if `in_reply_to_user_id` on the reply matches the `author_id` of the tweet_id we are interested in.

                    # Let's assume any reply in the conversation not by the original author is a "comment"
                    # A more precise filter could be to ensure reply.in_reply_to_tweet_id (if available via different endpoint/expansion)
                    # or checking the conversation structure.
                    # For now, this is a broader catch within the conversation.
                    if reply.id != tweet_id: # Make sure it's not the original tweet itself
                         comments_on_specific_tweet.append(reply)

            if comments_on_specific_tweet:
                print(f"  Found {len(comments_on_specific_tweet)} potential comments for tweet {tweet_id}.")
            else:
                print(f"  No direct comments found for tweet {tweet_id} with the current filtering.")
            return comments_on_specific_tweet

        except tweepy.TweepyException as e:
            print(f"  Error fetching comments for tweet {tweet_id}: {e}")
            if response and response.errors:
                print(f"  API Errors: {response.errors}")
            return []
        except Exception as e:
            print(f"  An unexpected error occurred while fetching comments: {e}")
            return []

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    # Ensure TWITTER_BEARER_TOKEN is set in your environment or .env file
    client = TwitterClient()
    # Replace with the actual Twitter handle or name for Bahrain Airport Company
    # And potentially get their user ID for more precise filtering if needed.
    # For example, you might want to look up "@BAC_Bahrain" user ID first.
    test_query = '"Bahrain Airport Company" OR @BAC_Bahrain -is:retweet'
    mentions = client.get_mentions(query=test_query, max_results=5)

    if mentions:
        for mention in mentions:
            print(f"\nMention Tweet ID: {mention.id} by Author ID: {mention.author_id} | Text: {mention.text}")
            # Pass the author_id of the tweet that *contained* the mention
            comments = client.get_comments_on_tweet(mention.id, mention.conversation_id, mention.author_id, max_results=5)
            if comments:
                for comment in comments:
                    print(f"    Comment ID: {comment.id} | Author ID: {comment.author_id} | Text: {comment.text}")
            else:
                print("    No comments retrieved for this mention.")
    else:
        print("No mentions found to test comment retrieval.")