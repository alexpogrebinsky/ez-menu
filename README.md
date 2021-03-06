# EZ Menu

A simple menu making application that stores User data and menu data in a MySQL database and publishes menus to public objects on Google Storage. Uses Firebase
Authentication, Google App Engine, Google Cloud SQL and Google Storage.

You'll need to have [Python 2.7](https://www.python.org/) and the [Google Cloud SDK](https://cloud.google.com/sdk/?hl=en)
installed and initialized to an App Engine project before running the code in
this sample.

## Setup

1. Clone this repo:

        git clone https://github.com/dylanrdrake/ez-menu.git

1. Navigate to the backend directory:

        cd ez-menu/backend

1. Install the 3rd-party dependencies to the backend service:

        pip install -t lib/ -r requirements.txt

    if you get python3 print statement error, remove * in lib/, install pip2.7 and:

        pip2.7 install -t lib/ -r requirements.txt

1. To access Cloud SQL:

    - create file: backend/env_config.py to store sensitive logins, passwords and keys. The .gitignore will block these from being pushed to Github.


1. [Add Firebase to your app.](https://firebase.google.com/docs/web/setup#add_firebase_to_your_app)
1. Add your Firebase project ID to the backend’s `app.yaml` file as an
environment variable.
1. Select which providers you want to enable. Delete the providers from
`main.js` that you do no want to offer. Enable the providers you chose to keep
in the Firebase console under **Auth** > **Sign-in Method** >
**Sign-in providers**.
1. In the Firebase console, under **OAuth redirect domains**, click
**Add Domain** and enter the domain of your app on App Engine:
[PROJECT_ID].appspot.com. Do not include "http://" before the domain name.

## Run Locally
1. Install AppEngine included libaries listed in backend/app.yaml into your system python:

        pip install <package>

    These will automatically be imported into the runtime when deployed to AppEngine 

1. Add the backend host URL to `main.js`: http://localhost:8081.

1. Navigate to the root directory of the application and start the development
server with the following command:

        dev_appserver.py frontend/app.yaml backend/app.yaml

1. Visit [http://locahost:8080/](http://locahost:8080/) in a web browser.

## Deploy
1. Change the backend host URL in `main.js` to
https://backend-dot-[PROJECT_ID].appspot.com.
1. Deploy the application using the Cloud SDK command-line interface:

        gcloud app deploy backend/index.yaml frontend/app.yaml backend/app.yaml

    The Cloud Datastore indexes can take a while to update, so the application
    might not be fully functional immediately after deployment.

1. View the application live at https://[PROJECT_ID].appspot.com.


## TODO
1. Create sharing code.

2. Create theme options and code.

3. Alert me when this menu changes:
- Twilio docs in Google Cloud docs or Firebase messaging
- link on published menu to app page where user can enter phone number
- Take a look a cron jobs and how they could be utilized

4. What are people posting ticker

5. Colorscheme:
    colorscheme: #11353B, #4ecdc4, #f7fff7, #ff6b6b, #ffe66d

6. style the color selectors as circles

7. Kiosks: put code on back of pi. Set up local network site on pi that user can enter in wifi password. Have Set up Kiosk feature in web UI.

8. Load menus via Ajax direct from db instead of hosting on storage? Don't require auth when hitting /menus GET with menuid (has to be public).
