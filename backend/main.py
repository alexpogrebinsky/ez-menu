#-*- coding: utf-8 -*-

# 
import logging
from flask import Flask,request,url_for,redirect,render_template,g,jsonify
import flask_cors
import google.auth.transport.requests
import google.oauth2.id_token
import requests_toolbelt.adapters.appengine
from datetime import datetime
# CloudSQL
import os
import MySQLdb as mysql
from env_config import creds
# Storage
import cloudstorage as gcs
from google.appengine.api import app_identity

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()
HTTP_REQUEST = google.auth.transport.requests.Request()

app = Flask(__name__)
# allows Ajax
flask_cors.CORS(app)

# Get Storage bucket
bucket = os.environ.get('BUCKET_NAME',
        app_identity.get_default_gcs_bucket_name())



@app.before_request
def db_connect():
    if (os.getenv('SERVER_SOFTWARE') and \
            os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')):
        g.conn = mysql.connect(unix_socket='/cloudsql/'+creds['_INSTANCE_NAME'],
                               db=creds['dbbase'],
                               user=creds['dbuser'],
                               passwd=creds['dbpass'])
    else:
        # this is the database used when running dev_appserver.py
        g.conn = mysql.connect(host=creds['dbhost'],
                               db=creds['dbbase'],
                               user=creds['dbuser'],
                               passwd=creds['dbpass'])


@app.teardown_request
def db_disconnect(exception):
    g.conn.close()



# Query Database
def query_db(sql_query, commit):
    cursor = g.conn.cursor()
    cursor.execute(sql_query)
    raw_results = cursor.fetchall()
    column_data = cursor.description
    cursor.close()
    if commit:
        g.conn.commit()
        return True

    columns = [col[0] for col in column_data]
    results = [{col: data for col,data in zip(columns,result)}\
            for result in raw_results]

    return results



# Check Authorization
def auth_check(request):
    # Verify Firebase auth.
    id_token = request.headers['Authorization'].split(' ').pop()
    claims = google.oauth2.id_token.verify_firebase_token(
        id_token, HTTP_REQUEST)
    if not claims:
        return 'Unauthorized', 401

    # Update User or Create User if none exists
    if get_user(claims.get('user_id')):
        update_user(userid=claims.get('user_id'),
                    provider=claims.get('firebase')['sign_in_provider'],
                    name=claims.get('name'),
                    email=claims.get('email'),
                    picture=claims.get('picture'))
    elif not get_user(claims.get('user_id')):
        create_user(userid=claims.get('user_id'),
                    provider=claims.get('firebase')['sign_in_provider'],
                    name=claims.get('name'),
                    email=claims.get('email'),
                    picture=claims.get('picture'))
    
    return claims.get('user_id')



# Get User
def get_user(userid):
    user_query = """
    SELECT * FROM Users
    WHERE UserId = '{0}'
    """.format(userid)
    user_data = query_db(user_query, False)
    return user_data


# Create User
def create_user(userid, provider, name=None, email=None, picture=None):
    create_user_sql = """
    INSERT INTO Users
    (UserId, AuthProvider, Name, Email, Picture)
    VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')
    """.format(userid, provider, name, email, picture)
    user_created = query_db(create_user_sql, True)
    return user_created


# Update User
def update_user(userid, provider, name=None, email=None, picture=None):
    update_user_sql = """
    UPDATE Users
    SET AuthProvider='{0}',
        Name='{1}',
        Email='{2}',
        Picture='{3}'
    WHERE UserId='{4}'
    """.format(provider, name, email, picture, userid)
    query_db(update_user_sql, True)
    return redirect(url_for('menus'))




# Create Menu route
@app.route('/createmenu', methods=['POST', 'PUT'])
def createmenu(userid, menujson):
    userid = auth_check(request)
    menu = json.loads(menujson)
    items = menu['items']

    if request.method == 'POST':
        menu['menuid'] = datetime.utcnow().strftime('%y%m%d%H%M%S%f')
        create_menu_sql = """
        INSERT INTO menus
        (MenuId, MenuTitle, Owner, Theme, PageInterval, ShareWith)
        VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')
        """.format(menu['menuid'], menu['title'], menu['userid'],
                menu['theme'], menu['pageinterval'], menu['sharewith'])
        query_db(create_menu_sql, True)

        for item in items:
            create_item_sql = """
            INSERT INTO items
            (MenuId, ItemTitle, ItemDesc,
            ItemPrice, ItemCurrency, ItemOrdering)
            VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')
            """.format(menu['menuid'], item['itemtitle'], item['itemdesc'],
                    item['itemprice'], item['itemcurr'], item['itemord'])
            query_db(create_item_sql, True)

    elif request.method == 'PUT':
        update_menu_sql = """
        UPDATE menus
        SET Title='{0}',
            Theme='{1}',
            PageInterval='{2}',
            ShareWith='{3}',
        WHERE MenuId='{4}'
        """.format(menu['title'], menu['theme'], menu['pageinterval'],
                menu['sharewith'], menu['menuid'])
        query_db(update_menu_sql, True)

        for item in items:
            update_item_sql = """
            UPDATE items
            SET ItemTitle='{0}',
                ItemDesc='{1}',
                ItemPrice='{2}',
                ItemCurrency='{3}',
                ItemOrdering='{4}'
            WHERE ItemId='{5}'
            """.format(item['itemtitle'], item['itemdesc'], item['itemprice'],
                    item['itemcurr'], item['itemord'], item['itemid'])
            query_db(update_item_sql, True)

    if menu['publish']:
        publiclink = publish_menu(menu['menuid'])
        update_link_sql = """
        UPDATE menus
        SET PublicLink='{0}'
        WHERE MenuId='{1}'
        """.format(publiclink, menu['menuid'])
        query_db(update_link_sql, True)
  
    if menu['takedown']:
        takedown_menu(menu['menuid'])
        takedown_link_sql = """
        UPDATE menus
        SET PublicLink=NULL
        WHERE MenuId='{0}'
        """.format(menu['menuid'])
        query_db(takedown_link_sql, True)


    return redirect(url_for('menus'))




# Get Menu
def get_menu(menuid):
    item_query = """
    SELECT * FROM items
    WHERE MenuId='{0}'
    """.format(menuid)
    item_data = query_db(item_query, False)

    menu_query = """
    SELECT * FROM menus
    WHERE MenuId={0}
    """.format(menuid)
    menu_data = query_db(menu_query, False)

    menu_data['items'] = item_data

    return jsonify(menu_data)


# Publish Menu
def publish_menu(menuid):
    menu_data = get_menu(menuid)

    menuHTML = render_template('menu_template.html',
                               menu_data=menu_data)

    object = '/'+bucket+'/menus/'+menuid+'.html'

    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
    with gcs.open(object,
                  'w',
                  content_type='text/html',
                  options={'x-goog-acl': 'public-read'},
                  retry_params=write_retry_params) as menu_file:
        menu_file.write(str(menuHTML))
        menu_file.close()
 
    menu_link = 'https://storage.googleapis.com/ez-menu.appspot.com/menus/'+filename

    return menu_link


# Take down menu
def takedown_menu(menuid):
    object = '/'+bucket+'/menus/'+menuid+'.html'
    gcs.delete(object)


# get menus
@app.route('/menus', methods=['GET'])
def menus():
    userid = auth_check(request)

    menus_query = """
    SELECT * FROM menus
    WHERE Owner='{0}'
    """.format(userid)
    
    menus_data = query_db(menus_query, False)

    return jsonify(menus_data)






@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
# [END app]
