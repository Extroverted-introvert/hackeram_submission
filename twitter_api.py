import tweepy


def get_tweet_sentiment(city):
        
    auth = tweepy.OAuthHandler("sWHOzqDwM3UbT7XqQcKvR2wku", "t2OYKAbry0knI1VSaWLtOTsE18dqiE0yQdc6kwIFg5wj9TRJ8U")
    auth.set_access_token("810538727944704000-r5YCr88V4A86dUbJx0fl9I02sPRee86", "cWWmdGCuVrPjNQb3hI5dwijmb4Z7l3Us4yjGv8CsGJHx3")
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
