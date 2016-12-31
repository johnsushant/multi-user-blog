from google.appengine.ext import db

# Model for storing details of a blog 
class BlogPost(db.Model):
    title = db.StringProperty(required = True)
    username = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    # StringProperty was used for likes and dislikes because Jinja seemed
    # to have issues outputting IntegerProperty
    likes = db.StringProperty(default = '0')
    dislikes = db.StringProperty(default = '0')

# Model for storing details of a comment
class Comment(db.Model):
    username = db.StringProperty(required = True)
    post_id = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

# Model for storing details of a user
class User(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    verify = db.StringProperty(required = True)
    email = db.StringProperty(required = True)
    postliked = db.StringListProperty()