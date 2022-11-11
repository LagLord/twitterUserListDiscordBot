import datetime
import time
from threading import Thread, enumerate
import tweepy
import pandas
from config import *
from discord import Webhook, SyncWebhook, Embed
import json

webhook = SyncWebhook.from_url(
    webhook_url
    )  # Initializing webhook


# Importing discord.Webhook and discord.RequestsWebhookAdapter as well as Embed class
def send_tweet(msg, author, media):
    embed = Embed(title="\u200B", description=f"{msg['text']}", timestamp=datetime.datetime.strptime(msg['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                  colour=0xA020F0)  # Initializing an

    embed.add_field(name="Likes:", value=f"{msg['public_metrics']['like_count']}")  # Adding a new field
    embed.add_field(name="Retweets:", value=f"{msg['public_metrics']['retweet_count']}")  # Adding a new field
    embed.set_author(name=f'{author["name"]}(@{author["username"]})', icon_url=author['profile_image_url'],
                     url=author['profile_image_url'])
    embed.set_footer(text=f'Twitter', icon_url="https://images-ext-1.discordapp.net/external"
                                               "/bXJWV2Y_F3XSra_kEqIYXAAsI3m1meckfLhYuWzxIfI/https/abs.twimg.com"
                                               "/icons/apple-touch-icon-192x192.png")
    try:
        embed.set_image(url=media['url'])
    except:
        try:
            embed.set_image(url=media['preview_image_url'])
        except:
            pass
        print("No url")

    webhook.send(content=main_msg, embed=embed)  # Executing webhook and sending embed.


class TweetListener(tweepy.StreamingClient):

    def on_data(self, tweet):
        tweet = json.loads(tweet)
        print(tweet)
        print(tweet['data'], tweet['includes']['users'][0])
        try:
            mediaOb = tweet['includes']['media'][0]
        except:
            mediaOb = {}
        send_tweet(tweet['data'], tweet['includes']['users'][0], mediaOb)

    def on_closed(self, response):
        print(response)


def run_tweet_grabber(resend_rules=False):
    rules = None
    stream = TweetListener(bearer_token=Bear_token)

    current_rule_ids = [i.id for i in stream.get_rules().data]
    print('all rules: ', current_rule_ids)
    print(stream.delete_rules(ids=current_rule_ids))

    print(stream.running)
    # stream.filter(follow=['paadsingh400'])
    for i in range(0, len(rules)):
        new_r = stream.add_rules(tweepy.StreamRule(rules[i], id=str(i)))
        print('rule: ', new_r)

    all_rules = stream.get_rules().data
    print('all rules: ', len(all_rules), all_rules)
    print(stream.filter(expansions=["author_id", "attachments.media_keys"],
                        tweet_fields=['attachments', 'public_metrics', 'created_at', 'author_id'],
                        user_fields=['profile_image_url', 'username'],
                        media_fields=['url', 'preview_image_url']))


def get_data_from_spreadsheet():
    df = pandas.read_csv(pathtoCsv)
    # handles_list = [str(i) for i in df['Handles'].dropna().tolist()]
    messages_list = [str(i) for i in df['Message'].dropna().tolist()]

    # rules_list = []

    single_rule = ""
    # for handle in handles_list:
    #     # if handle == handles_list[-1]:
    #     #     single_rule = single_rule + f'from:{handle}'
    #     # else:
    #     #     single_rule = single_rule + f'from:{handle} OR '
    #     single_rule = handle
    #     rules_list.append(single_rule)
    #     print(single_rule, len(single_rule))
    #
    #     # Checking if length of the rule is less than 512
    #
    #     # if 8 <= len(single_rule) < 512:
    #     #     rules_list.append(single_rule)
    #     #     single_rule = ""

    return messages_list[0]



# print(rules)

# tweet_thread = Thread(target=run_tweet_grabber, args=())
# tweet_thread.daemon = True
# tweet_thread.start()

next_token = None
max_tweets = 10
past_tweet_ids = []
hour = -1

client = tweepy.Client(
    Bear_token,
    return_type=dict
)

while True:
    result = client.get_list_tweets(id='7450', expansions=["author_id", "attachments.media_keys"],
                                    tweet_fields=['attachments', 'public_metrics', 'created_at', 'author_id'],
                                    user_fields=['profile_image_url', 'username'],
                                    media_fields=['url', 'preview_image_url'], max_results=max_tweets,
                                    pagination_token=next_token)
    # next_token = result['meta']['previous_token']
    cur_hour = datetime.datetime.now().hour
    if hour != cur_hour:
        main_msg = get_data_from_spreadsheet()
        hour = cur_hour

    tweet_data = result['data']

    user_data = result['includes']['users']
    try:
        media_data = result['includes']['media']
    except:
        media_data = []

    print(result, "Next token: ", result['meta'])

    print('Tweet DATA: ', len(tweet_data), tweet_data[0])
    print('USERS DATA: ', len(user_data), user_data[0])
    # print('MEDIA DATA: ', len(media_data), media_data[0])

    for tweet in tweet_data:

        if tweet['id'] in past_tweet_ids:
            continue

        author_id = tweet['author_id']
        if 'attachments' in tweet:
            try:
                media_key = tweet['attachments']['media_keys'][0]
                media_tweet = [i for i in media_data if i['media_key'] == media_key][0]
            except:
                media_tweet = {}

        else:
            media_tweet = {}

        user = [i for i in user_data if i['id'] == author_id][0]

        send_tweet(tweet, user, media_tweet)
        past_tweet_ids = [i['id'] for i in tweet_data]

    time.sleep(12)
# while True:
#     time.sleep(3600)
#
#     new_rules, main_msg = get_data_from_spreadsheet()
#
#     if set(new_rules) != set(rules):
#         print("Adding new rules...")
