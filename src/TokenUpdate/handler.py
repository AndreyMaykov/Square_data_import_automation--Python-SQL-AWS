import token_update as tu

token_update = tu.TokenUpdate()

def lambda_handler(event, context):
    token_update.db_connection
    token_update.update_access_tokens()
    token_update.db_connection.close()