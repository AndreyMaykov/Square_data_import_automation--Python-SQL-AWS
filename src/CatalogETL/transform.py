import json
from functools import cache
import misc as ms
import attribute_dict as ad

class Transform:
    def __init__(self, ctlg):
        self.ctlg = ctlg

    def cat_sublist(self, type_value):
        y = [x for x in self.ctlg if x['type'] == type_value]
        return y

    def column_name_list(self, attrib_dict):
        y = list(attrib_dict.keys())
        y.insert(0, 'merchant_id')
        return y

class TransformProducts(Transform):
    # A class used for transforming the product data 
    # containg in the catalog retrieved from Square 
    # before loading into the destination DB
    def __init__(self, ctlg, ctlg_prods_vars, merchant_id):
        super().__init__(ctlg)
        self.merchant_id = merchant_id
        self.ctlg_prods_vars = ctlg_prods_vars


    @property
    @cache
    def category_list(self):
        # List (comprised of dictionaries) that provides descriptions
        # of all the categories and their attributes used in the merchant's catalog.
        y = self.cat_sublist("CATEGORY")
        return y

    @property
    @cache
    def category_dict(self):
        # Dictionary with key-value pairs where the key is the id of a category
        # and the value is the category's name.
        y = ms.rev_dict(self.category_list, 'id', ['category_data', 'name'])
        return y

    @property
    def products_col_name_list(self):
        # List of the column names of the products table in the destination DB
        y = self.column_name_list(ad.PRODUCT_ATTRIBUTE_DICT)
        return y

    def product_data_transform_0(self, product):
        # For a product in the merchant's catalog, create a list of values
        # corresponding to product_col_name_list
        y = {}
        y['merchant_id'] = self.merchant_id
        for key, value in ad.PRODUCT_ATTRIBUTE_DICT.items():
            y[key] = ms.get_nested(product, value)
            # print("key = ", key, "; y = ", y[key])
        return z

    def product_data_transform(self, product):
        # For a product in the merchant's catalog, create a list of values
        # corresponding to product_col_name_list
        y = {}
        y['merchant_id'] = self.merchant_id
        for db_attr_name, cat_val_path in ad.PRODUCT_ATTRIBUTE_DICT.items():
            y[db_attr_name] = ms.get_nested(product, cat_val_path)
            # print("key = ", key, "; y = ", y[key])
        y['category_orig'] = ms.get_nested(self.category_dict, [y['category_orig']])
        z = list(y.values())
        return z

    @property
    def products_data(self):
        # Nested list of values for attributes of the products table
        # of the destination DB. Each sublist comprises values for
        # one product in the merchant's catalog
        y = [self.product_data_transform(x) for x in self.ctlg_prods_vars]
        return y

class TransformVariations(Transform):
    # A class used for transforming the product variations data 
    # containg in the catalog retrieved from Square 
    # before loading into the destination DB
    def __init__(self, ctlg, ctlg_prods_vars, merchant_id):
        super().__init__(ctlg)
        self.merchant_id = merchant_id
        self.ctlg_prods_vars = ctlg_prods_vars

    @property
    @cache
    def option_list(self):
        # List of all the options and their attributes (including option values)
        # used in the merchant's catalog
        y = [x for x in self.ctlg if x['type'] == "ITEM_OPTION"]
        return y

    @property
    @cache
    def option_dict(self):
        # Dictionary with key-value pairs where the key is an option's id
        # and the value is a dictionary providing the option's name along
        # with all the option's value id's and names
        y = {}
        for x in self.option_list:
            y[x['id']] = {
                'name': x['item_option_data']['name'],
                'values': ms.rev_dict(x['item_option_data']['values'], 'id', ['item_option_value_data', 'name'])
            }
        return y

    @property
    def variations_col_name_list(self):
        # List of the column names of the variations table in the destination DB
        y = self.column_name_list(ad.VARIATION_ATTRIBUTE_DICT)
        return y

    def variation_data_transform(self, product_variation):
        # For a product variation in the merchant's catalog, create
        # a list of values corresponding to variations_col_name_list.
        # The value for variation_description attribute is a string
        # describing all the product option values corresponding
        # to this product variation
        y = {}
        y['merchant_id'] = self.merchant_id
        for key, value in ad.VARIATION_ATTRIBUTE_DICT.items():
            y[key] = ms.get_nested(product_variation, value)
        if type(y['price']) != str:
            # y['price'] = str(y['price']/100)
            y['price'] = y['price'] / 100    # EXPLAIN
        var_desc = 'N/A'
        orig_desc = y['variation_description']
        if orig_desc != 'N/A':
            var_desc = ""
            for k in range(len(orig_desc)):
                a = orig_desc[k]['item_option_id']
                b = orig_desc[k]['item_option_value_id']
                var_desc = var_desc + self.option_dict[a]['name'] + ": " + self.option_dict[a]['values'][b] + "; "
        y['variation_description'] = var_desc
        z = list(y.values())
        return z

    @property
    def variations_data(self):
        # Nested list of values for attributes of the product_variations table
        # of the destination DB. Each sublist comprises values for one variation
        # of one product in the merchant's catalog
        z = [
            self.variation_data_transform(y)
            for item in self.ctlg_prods_vars
            for y in ms.get_nested(item, ['item_data', 'variations'])
        ]
        return z