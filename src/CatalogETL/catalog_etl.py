import json
import extract as ex
import load as ld


def catalog_etl(event):
    event_body = json.loads(event['body'])
    req_type = event_body['type'] # initial import or updating store data
    extr =  ex.Extract(event_body)
    if req_type == 'catalog.request': # initial import
        extr =  ex.Extract(event_body)
        ld.load_init(extr.ctlg, extr.ctlg_prods_vars, extr.merchant_id)
        w = f"""
            Initial catalog import completed (merchant_id = 
            {extr.merchant_id})
        """
    elif req_type == 'catalog.version.updated': # updating store data
        ld.load_upd_del(extr.ctlg, extr.ctlg_prods_vars, extr.merchant_id)
        w = f"""
            Updated catalog loaded (merchant_id = 
            {extr.merchant_id})
        """
    else:
        w = "Incorrect request type"
    return w