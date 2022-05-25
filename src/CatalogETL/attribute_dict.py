# Comprises all the key-value pairs p_name: p_value_path where 
# p_value_path is the key path to a product attribute value 
# in the catalog retrieved from Square and
# p_name is the name of the column of the products table 
# where such attribute values are loaded
PRODUCT_ATTRIBUTE_DICT = {
    'product_name': ['item_data', 'name'],
    'product_orig_id': ['id'],
    'description': ['item_data', 'description'], 
    'category_orig': ['item_data', 'category_id']
}

# Comprises all the key-value pairs pv_name: pv_value_path where 
# pv_value_path is the key path to a product variation attribute value 
# in the catalog retrieved from Square and
# pv_name is the name of the column of the product_variations table 
# where such attribute values are loaded
VARIATION_ATTRIBUTE_DICT = {
    'product_orig_id': ['item_variation_data', 'item_id'],
    'variation_orig_id': ['id'],
    'price': ['item_variation_data', 'price_money', 'amount'],
    'currency': ['item_variation_data', 'price_money', 'currency'],
    'variation_description': ['item_variation_data', 'item_option_values']
}