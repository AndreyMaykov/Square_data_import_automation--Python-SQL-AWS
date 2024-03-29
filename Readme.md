# Square Data Import Automation Project
**The Square Data Import Automation project (SDIAP)** aims at developing an automated system for importing data from multiple Square online stores into a destination database. The importation process involves transforming the original data to comply with the specifications of the destination DB. Also, the system ensures automatic data synchronization: whenever a participating merchant alters the catalog of their Square online store, the data in the destination DB is updated accordingly.
#### Project background
Initially, the Square Data Import system was meant to facilitate operating <a href="https://github.com/AndreyMaykov/Online_marketplace_shipping__SQL">an online marketplace</a> (further referred to as **OM**), which was under development at the time. It was expected that some of the vendors participating in OM might also offer their products on other platforms (e.g. Square, Shopify, Squarespace), so the goal of SDIAP was to ensure catalog consistency between OM and the Square platform. This determined the requirements to the data import system and, up to a point, its design.

## Contents
[Technologies](#technologies) <br />
[Destination database](#destinationDB) <br /> 
[Catalog JSON string generated by Square](#JSON_strng) <br />
  [The string structure](#string_structure) <br />
  [Attribute names and values](#naming) <br />
[Obtaining, transforming and loading data](#RTL) <br />
  [TokenUpdate: Managing access tokens](#tokens) <br />
  [CatalogETL: Initial catalog import](#initial_import) <br />
  [CatalogETL: Updating store data in the DB](#updating_data) <br />
[Further development](#further_development) <br />
[Acknowledgements](#acknowledgements) <br />

<a name="technologies"><h2>Technologies</h2></a>
- Python 3.8 / PyCharm 2022.3.1
- MySQL 8.0.27 / MySQL Workbench 8.0.28
- AWS 
  - AWS Lambda 
  - API Gateway
  - EventBridge / CloudWatch Events
  - RDS
- <a href="https://developer.squareup.com/ca/en">Square Developer Tools</a>
  - Square APIs
  - Webhooks
  - Square implementation of the OAuth 2.0 protocol
- <a href="https://squareup.com/help/us/en/article/6852-get-started-with-square-online-store">Square Online</a> 

<a name="destinationDB"><h2>Destination database</h2></a>
This simple database emulates the features and functionalities of the devised OM DB that are essential for obtaining data from the Square platform.

![ ](https://github.com/AndreyMaykov/Square_data_import_automation__Python-SQL-AWS/blob/main/images/DB_ER_diagram.png) 

The table `tokens` is used to store tokens required for requesting information from the Square online stores.

The table `products` contains the most general information related to the products available at the stores: the name of the product, its category and the description which the merchant provided.

The table `product_variations` contains more specific details about the whole variety of variations of each product, e.g. available sizes and colours, as well as the price of each variation.

<a name="temp_tables"><h4>The temp tables</h4></a>

When an updated store catalog is received from Square, the tables `products_temp` and `product_variations_temp` are used 
to update the information related to the store in the `products` and `product_variations` tables. Thus the destination DBMS engine is utilized instead of looping through the DB rows, which enhances the system's performance.

<a name="JSON_strng"><h2>Catalog JSON string</h2></a>

<a name="string_structure"><h3>The string structure</h3></a>

In a catalog JSON string generated by Square, descriptions of the products and their variations often use IDs instead of explicit attribute names and values (for example, <code>category_id: 24NQR42J3F76MPLL7VYKCTAZ</code> instead of <code>category: Cross Country Spikes</code>).

Information for decoding these IDs is located in the catalog string separately from the product and variation descriptions, which results in a complex nested JSON structure of the catalog string. 
<a href="https://github.com/AndreyMaykov/Square_data_import_automation__Python-SQL-AWS/blob/main/docs/catalog_example.txt">An example catalog JSON string</a> and 
<a href="https://github.com/AndreyMaykov/Square_data_import_automation__Python-SQL-AWS/blob/main/docs/catalog_example_diagram.png">its diagram</a>
demonstrate this complexity in the case of an online store which offers two products.

To avoid unnecessary data redundancy in the destination DB, the data structure in SDIAP is transformed: relations between attributes and their values are converted into direct ones (i.e. not involving intermediary IDs). 

<a name="naming"><h3>Attribute names and values</h3></a>
<p>
The Square platform is very flexible in terms of naming attributes and defining their values. For example, a merchant is free to use any set of category names to categorize products offered at their online store. Other attribute names, such as options, and attribute values are also defined arbitrarily by the merchant.
</p>
<p>
Due to this, the total number of attribute names and values used in all the Square stores participating in OM can, in theory, be as large as the total number of the products and their variations.
</p>
<p>
On the other hand, the OM project database utilizes a unified (and reasonably limited) attribute system to provide effective product search in the database.
Therefore, importing product data from Square with their attributes just being added to the OM system might cause an overwhelming growth of the system and completely undermine the OM product search process.
</p>
<p>
Replacing Square attributes with their OM analogs sounds like a natural solution. However, determining such analogs is somewhat similar to product categorization, which is well-known as a difficult problem requiring sophisticated methods for automation. Dealing with such complex methods was not an option at this stage of SDIAP, so a simple substitute was adopted: storing Square attribute names and values in the destination DB as text – unless they can be interpreted with no difficulty, like product prices. This approach still provides some product search capabilities, though the efficiency of the search process might be low.
</p>


<a name="RTL"><h2>Obtaining, transforming and loading data</h2></a>

Two AWS Lambda functions – 
<a href="https://github.com/AndreyMaykov/Square_data_import_automation__Python-SQL-AWS/blob/main/src/CatalogETL/">**CatalogETL**</a> 
and 
<a href="https://github.com/AndreyMaykov/Square_data_import_automation__Python-SQL-AWS/blob/main/src/TokenUpdate/">**TokenUpdate**</a>
– were created to carry out SDIAP data manipulations.

<a name="tokens"><h3>TokenUpdate: Managing access tokens</h3></a>

<a name="access_maintaining"><h4>How access to Square data is maintained</h4></a>

The Square platform uses 
the <a href = "https://tools.ietf.org/html/rfc6749">OAuth 2 protocol</a> 
to control application access to the hosted online stores. Therefore, receiving data from a store via an HTTP request is only possible if the application sending the request is authorized, which means an access token was issued to the application. The token must be included in the request. 

An access token has a limited lifetime and must be replaced with a new token before expiring so that the access is maintained. To have an access token replaced, one needs to send a special HTTP request with a so-called refresh token embedded.

For each Square store, the refresh token is issued to an application only once (this happens when the application is authorized) and never expires.

<a name="access_maintaining_SDIAP"><h4>Access maintenance implementation in SDIAP</h4></a>

In SDIAP, the process of refreshing access tokens for all the Square stores involved is automated.

Basically, the process comprises the following steps:

- retrieving the refresh token for each store from the table `tokens`;
- requesting and receiving the new access tokens from Square;
- replacing the access tokens stored in the table `tokens` with the new tokens.

TokenUpdate handles all these steps. To do so, it requires the application’s client ID and client secret, the Square API endpoint, as well as credentials for accessing the destination DB. Part of this data is stored in the table `tokens`, the rest – in the
<a href="https://github.com/AndreyMaykov/Square_data_import_automation__Python-SQL-AWS/blob/main/src/TokenUpdate/connection_param.py">connection_param.py</a> file.

TokenUpdate is invoked by AWS EventBridge on a schedule that can be altered if needed.


<a name="initial_import"><h3>CatalogETL: Initial catalog import</h3></a>

After a new Square store joins OM or SDIAP and the access token for the store has been loaded into the database, it is possible to import the store catalog for the first time. In the current version of SDIAP, this process is initiated manually by the administrator. 

To do so, the admin sends an HTTP POST request with a body specifying the store merchant ID and the request type (the latter must be <code>"catalog.request")</code>. The request is processed by the CatalogETL API, which triggers the CatalogETL function. Further stages of the process are shown in the diagram below; all of them are managed by CatalogETL.

![ ](https://github.com/AndreyMaykov/Square_data_import_automation__Python-SQL-AWS/blob/main/images/ctlg_import.svg)

To transform the catalog data as discussed [above](#string_structure), two dictionaries – <a href="https://github.com/AndreyMaykov/Square_data_import_automation__Python-SQL-AWS/blob/main/src/CatalogETL/attribute_dict.py">PRODUCT_ATTRIBUTE_DICT and VARIATION_ATTRIBUTE_DICT</a> –   are used. 
They define: 
- the set (which can be changed if needed) of the attributes imported from Square catalogs;
- mappings between attribute names in the `products`/`product_variations` table and the corresponding values in catalog strings received from Square.

Some of the data processing operations involved in the process may be resource-consuming. Therefore, if the result of such an operation is used more than once, it is cached after the operation is carried out for the first time.


<a name="updating_data"><h3>CatalogETL: Updating store data in the DB</h3></a>

This process is similar to initial importation, except for the following.

First, it is invoked automatically by <a href="https://developer.squareup.com/docs/catalog-api/webhooks">a Square webhook</a> that sends an HTTP POST request when the store catalog is updated in any way. The request includes <code>"type":" catalog.version.updated "</code> in its body (as well as the merchant_id corresponding to the store). 

![ ](https://github.com/AndreyMaykov/Square_data_import_automation__Python-SQL-AWS/blob/main/images/ctlg_load_upd_del.svg)

Another difference is that in the case of data updating, the transformed catalog data is first inserted not into the `products` and `product_variations` tables but into [the temp tables](#temp_tables). After that, a series of SQL queries are performed to change the records in products and product_variations that are identified by the same merchant_id so that they match those in products_temp and product_variations_temp.

For more detail about 
<a href="https://github.com/AndreyMaykov/Square_data_import_automation__Python-SQL-AWS/blob/main/src/CatalogETL/">CatalogETL</a> 
and 
<a href="https://github.com/AndreyMaykov/Square_data_import_automation__Python-SQL-AWS/blob/main/src/TokenUpdate/">TokenUpdate</a> 
AWS Lambda functions, see comments in the code.

<a name="further_development"><h2>Further development</h2></a>

The project needs implementing error-handling methods and security measures (such as encrypting Square store access credentials stored in the destination DB). 

The [above-mentioned](#naming) unconformity between the two attribute systems – used on the Square platform and in the destination DB – is another problem to deal with.

<a name="acknowledgements"><h2>Acknowledgements</h2></a>

I would like to thank Alek Mlynek for initiating this project as well as discussing it in depth and detail.

Due to the websites 
<a href="https://realpython.com/">realpython.com</a> and 
<a href=https://plantuml.com/json>plantuml.com</a>, I came across a lot of helpful materials and tools, and I am very grateful to the website creators and contributors. 



