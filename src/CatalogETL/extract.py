import pymysql
import requests
import json
import connection_param as cp
from functools import cache


class Extract:
    # When an HTTP request is received notifying that a Square merchant's catalog
    # has been updated, class Extract is used to retrieve the current version 
    # of the catalog
    
    def __init__(self,  event_body):
        self.event_body = event_body
        self.merchant_id = self.event_body['merchant_id']
        
    def sql_get_access_token(self) -> str:
        # SQL query. Used to retrieve the access token required for requesting 
        # the merchant's current catalog   
        st1 = "SELECT access_token FROM tokens WHERE merchant_id = \'"
        st2 = "\' AND client_id = \'" 
        y = st1 + self.merchant_id + st2 + cp.CLIENT_ID + "\'"
        return y
        
    def access_token(self) -> str:
        # HTTP request implementing sql_get_access_token()
        connection = pymysql.connect(host = cp.DB_ENDPOINT, user = cp.DB_USERNAME, password = cp.DB_PASSWORD, db = cp.DB_NAME, autocommit = True)
        cursor = connection.cursor()
        cursor.execute(self.sql_get_access_token())
        row = cursor.fetchone()
        connection.close()
        return row[0]
        
    @property
    @cache  
    def ctlg(self):
        # Request the merchant's current catalog and, upon receiving, convert it 
        # from a json string into a list of dictionaries.
        # The result is cached for a better overall peformance
        authorization = 'Bearer ' + self.access_token()
        headers = {
            'Square-Version': '2022-02-16',
            'Authorization': authorization, 
            'Content-Type': 'application/json',
        }
        response = requests.get(cp.CATALOG_LIST_ENDPOINT, headers = headers)
        data = response.text
        return json.loads(data)['objects']
    
    @property
    @cache    
    def ctlg_prods_vars(self):
        # Extract product descriptions from the catalog for further transformation.
        # The result is cached for a better overall peformance
        return [x for x in self.ctlg if x['type'] == "ITEM"]