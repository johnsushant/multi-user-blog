# Multi User Blog Website

The multi user blog website is a complete fully functional blog site which has been developed on Google's App Engine platform using Python. It makes use of Google Cloud Datastore as its database and Jinja 2 as its templating engine. It lists the blog posts on its front page has the following capabilities :-
  - Create, edit and delete blog posts
  - Create, edit and delete comments on these posts
  - Likes and dislikes on posts
  - Robust user registration system
  - Session management using cookies

### Installation

Multi user blog website requires [Python 2.7](https://www.python.org/)  and [Google App Engine Python Standard Environment](https://cloud.google.com/appengine/docs/python/) to run.
  - Install Python 2.7 and Google App Engine Python Standard Environment
  - Download and extract the zipped project.
  - Open command prompt and type the following command
```sh
    dev_appserver.py --clear_datastore=yes .
```
  - Go to [localhost:8080](http://localhost:8080/) to access the website.


### Architecture

The python code for the project resides in `main.py`
The templates used by jinja are present in the `/templates` folder.
The static files(css, javascript, images) are present in the `/static` folder.
