from catalog_etl import catalog_etl


def lambda_handler(event, context):

    return catalog_etl(event)