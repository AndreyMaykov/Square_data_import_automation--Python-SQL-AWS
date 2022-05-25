import misc as ms
import transform as tr
import pymysql
import connection_param as cp

# Functions used to change the destination DB records so that they match
# the latest catalog of an online store retrieved from Square.


# SQL queries:

def sql_delete_temp(merchant_id: str, table_name: str) -> str:
    # Remove the merchant's products or variations data from a temp table
    y = f"""DELETE FROM {table_name}_temp WHERE 
                merchant_id = {ms.sql_quotes(merchant_id)};"""
    return y

def sql_insert(table_name, column_names, raw_rows):
    # Insert catalog data rows into a table
    cn = '(' + ms.sql_column_names(column_names) + ')'
    sql_row_strings = ', \n'.join(map(ms.sql_values_row, raw_rows))
    y = f"""INSERT INTO {table_name} {cn} VALUES 
            {sql_row_strings};"""
    return y

def sql_upsert(table_name, column_names):
    # If a product/variation included in the merchant's latest catalog
    # already exists in the products/product_variations table, update the data;
    # if not, insert a new row with the information from the latest catalog.
    cn = ms.sql_column_names(column_names)
    c_as_new = ms.sql_column_names(list(map(ms.cast_as_new, column_names)))
    y = f"""INSERT INTO {table_name} {'(' + cn + ')'}
            SELECT {cn} FROM {table_name}_temp AS NEW 
                ON DUPLICATE KEY UPDATE {c_as_new};"""
    return y

def sql_delete_terminated(merchant_id, table_name, column):
    # Delete from products/product_variations all products/variations that
    # are no longer available through the merchant's Square online store
    y = f"""DELETE FROM {table_name}  WHERE 
                merchant_id = {ms.sql_quotes(merchant_id)} 
                AND 
                ({column} NOT IN (SELECT {column} FROM {table_name}_temp));"""
    return y

def load_init(ctlg, ctlg_prods_vars, merchant_id):
    # Initial importation of the data contained in the merchant's store catalog
    connection = pymysql.connect(
        host = cp.DB_ENDPOINT, user = cp.DB_USERNAME,
        password = cp.DB_PASSWORD, db = cp.DB_NAME, autocommit = True
    )
    cursor = connection.cursor()
    tr_prod = tr.TransformProducts(ctlg, ctlg_prods_vars, merchant_id)
    cursor.execute(
        sql_insert(
                "products", tr_prod.products_col_name_list,
                tr_prod.products_data
        )
    )
    tr_var = tr.TransformVariations(ctlg, ctlg_prods_vars, merchant_id)
    cursor.execute(
        sql_insert(
            "product_variations", tr_var.variations_col_name_list,
            tr_var.variations_data
        )
    )
    connection.close()

def load_upd_del(ctlg, ctlg_prods_vars, merchant_id):
    # Update the products/variations data related to the merchant's store
    connection = pymysql.connect(
        host = cp.DB_ENDPOINT, user = cp.DB_USERNAME,
        password = cp.DB_PASSWORD, db = cp.DB_NAME, autocommit = True
    )
    cursor = connection.cursor()
    tr_prod = tr.TransformProducts(ctlg, ctlg_prods_vars, merchant_id)
    cursor.execute(
        sql_delete_temp(merchant_id, "products")
    )
    cursor.execute(
        sql_insert(
                "products_temp", tr_prod.products_col_name_list,
                tr_prod.products_data
        )
    )
    cursor.execute(
        sql_upsert('products', tr_prod.products_col_name_list)
    )
    cursor.execute(
        sql_delete_terminated(merchant_id, "products", 'product_orig_id')
    )
    cursor.execute(
        sql_delete_temp(merchant_id, "products")
    )
    tr_var = tr.TransformVariations(ctlg, ctlg_prods_vars, merchant_id)
    cursor.execute(
        sql_delete_temp(merchant_id, "product_variations")
    )
    cursor.execute(
        sql_insert(
            "product_variations_temp", tr_var.variations_col_name_list,
            tr_var.variations_data
        )
    )
    cursor.execute(
        sql_upsert('product_variations', tr_var.variations_col_name_list)
    )
    cursor.execute(
        sql_delete_terminated(merchant_id, "product_variations", 'product_orig_id')
    )
    cursor.execute(
        sql_delete_terminated(
                merchant_id, "product_variations", 'variation_orig_id'
        )
    )
    cursor.execute(
        sql_delete_temp(merchant_id, "product_variations")
    )
    connection.close()
