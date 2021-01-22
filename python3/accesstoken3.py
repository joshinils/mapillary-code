from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session


client_id = 'd0FVV29VMDR6SUVrcV94cTdabHBoZzoxZjc2MTE1Mzc1YjMxNzhi'
token_url = "https://a.mapillary.com/v2/oauth/token"
redirect_uri = "https://geoclub.de/mapillary/oauth2.php"
auth_url = "https://www.mapillary.com/connect"
scopes = ['public:upload']

mobile = MobileApplicationClient(client_id)
oauth = OAuth2Session(client=mobile, redirect_uri=redirect_uri, scope=scopes)
authorization_url, state = oauth.authorization_url(url=auth_url)
print("State:", state)

print( 'Please go to %s and authorize access.' % authorization_url)
authorization_response = input('\nEnter the resulting callback URL:\n')

f = open("accesstoken3.conf", "w")
for line in authorization_response.split("&"):
    if "access_token" in line:
        f.write(line.split("=")[1])
f.close()
print("Configfile with access token created.")
