import pymysql
import requests
import json
import connection_param as cp
from functools import cache

class TokenUpdate:
    
    # A class used to update access tokens stored 
    # in the tokens table of the destination DB
    
    def __init__(self):
        pass

    @property
    @cache
    def db_connection(self):
        # Connection with the DB
        connection = pymysql.connect(
            host = cp.DB_ENDPOINT, user = cp.DB_USERNAME, 
            password = cp.DB_PASSWORD, db = cp.DB_NAME,
            autocommit = True
        )
        return connection

    @property
    @cache
    def get_refresh_tokens(self):
        # Retrieve from the DB refresh tokens 
        # for all the Square stores participating
        # in the project
        connection = self.db_connection
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM tokens;")
        rows = cursor.fetchall()
        refresh_tokens = [
            {
                'client_id': row[2], 
                'client_secret': row[3], 
                'grant_type': row[5], 
                'refresh_token': row[4]
            }
            for row in rows
        ]
        cursor.close()
        return refresh_tokens

    def update_access_tokens(self):
        # Request new access tokens for the stores
        # and replace the access tokens stored
        # in the DB with the new ones.
        headers = {'Square-Version': '2021-07-21'}
        for subdict in self.get_refresh_tokens:
            client_id = subdict['client_id']
            response = requests.post(
                cp.OAUTH2_ENDPOINT, 
                headers = headers, json = subdict
            )
            token_data = json.loads(response.text)
            sql_token_update = f"""UPDATE tokens SET 
                access_token = \'{token_data['access_token']}\', 
                access_token_expires = \'{token_data['expires_at']}\' 
                WHERE 
                refresh_token = \'{token_data['refresh_token']}\' AND 
                client_id = \'{client_id}\';
            """
            cursor = self.db_connection.cursor()
            cursor.execute(sql_token_update)
            cursor.close()