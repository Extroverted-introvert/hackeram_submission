# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client
from twitter_api import get_tweet_sentiment


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure

def send_twilio_message(username, country_code, target_number, location):
    target_number = "+" + str(country_code) + str(target_number)
    tweets = get_tweet_sentiment(location)
    if len(tweets)>5:
        data_dump = '\n'.join(tweets[:5])
    else:
        data_dump = '\n'.join(tweets)    
    account_sid = os.environ.get('account_sid')
    auth_token = os.environ.get('auth_token')
    client = Client(account_sid, auth_token)

    message = client.messages \
        .create(
            messaging_service_sid='MG4bbd0d80aa79771ca8041300a81f7981',
            body='Greetings {}, Location : {} \n{}'.format(username, location, data_dump),
            to=target_number
        )
    return message 
