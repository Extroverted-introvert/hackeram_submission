import os
import tweepy


def get_tweet_sentiment(city):
        
    auth = tweepy.OAuthHandler(os.environ.get('auth_token_1'), os.environ.get('auth_token_2'))
    auth.set_access_token(os.environ.get('auth_token_3'), os.environ.get('auth_token_4'))
    tweet_list = list()
    api = tweepy.API(auth)
    try:
        places = api.search_geo(query=city, granularity="city")
    except:
        places = api.search_geo(query="Delhi", granularity="city")    
    place_id = places[0].id
    print(place_id)
    tweets = api.search_tweets(q="covid-19 OR covid OR vaccination OR virus place:{} lang:en -has:links -has:media -has:images -has:videos -is:retweet".format(place_id), tweet_mode="extended")
    for i in range(len(tweets)):
        tweet_list.append("{}. ".format(i+1) + tweets[i].full_text + '\n')
    return tweet_list
