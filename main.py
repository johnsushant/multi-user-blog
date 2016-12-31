# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import webapp2
import jinja2
import re
import random
import hashlib
import hmac
import models

from google.appengine.ext import db

# Setting the template directory for jinja2
# Static files will be served from /static folder configured in app.yaml
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

# Code for encoding a cookie in the <name>|<hash> format
secret = 'temp'
def cookie_encode(s):
    return s + '|' + hmac.new(secret,s).hexdigest()

# Handler with boilerplate code
class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self,template,**params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    # Code for creating and deleting cookies
    def create_cookie(self, name, value):
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, str(cookie_encode(str(value)))))

    def delete_cookie(self, name):
        self.response.headers.add_header(
            'Set-Cookie','%s=%s; Path=/' % (name, ''))

    # Code for checking if cookie and its hash are valid
    def check_cookie(self, cookie_name):
        cookie = self.request.cookies.get(cookie_name)
        if not cookie:
            return ""
        username = cookie.split('|')[0]
        if not cookie_encode(username) == cookie:
            return ""
        else:
            return username

# Handles the creation of a new blog post
class NewPost(Handler):
    def get(self):
        username = self.check_cookie('username')
        if username:
            self.render('newpost.html', username=username)
        else:
            self.redirect('/login')

    def post(self):
        title = self.request.get('title')
        content = self.request.get('content')
        username = self.check_cookie('username')

        if not username:
            self.redirect('/login')
        else:
            if title and content:
                b = models.BlogPost(title=title, username=username, 
                content = content)
                b.put()
                # Prevent user from liking his own post
                u = db.GqlQuery("select * from User where username='%s'"
                % username).get()
                u.postliked.append(str(b.key().id()))
                u.put()
                # Redirect to permalink of new blog post
                self.redirect("/blog/" + str(b.key().id()))
            else:
                error = "Title and content cannot be left empty"
                self.render('newpost.html', title=title, content=content, 
                error = error)

# Handles the individual page of a blog post
class Blog(Handler):
    def get(self, key):
        username = self.check_cookie('username')
        
        # Finding specific blog content by ID
        post = models.BlogPost.get_by_id(int(key))

        # Finding comments on the blog post
        comments = db.GqlQuery("select * from Comment where post_id='%s'"
        % key).run()

        self.render('post.html', post=post, username=username, 
        comments = comments)

# Handles the deletion of a blog post
class DeletePost(Handler):
    def get(self, key):
        username = self.check_cookie('username')
        post = models.BlogPost.get_by_id(int(key))
        if username == post.username:
            db.delete(post.key())
        self.redirect('/login')

# Handles the editing of a blog post
class EditPost(Handler):
    def get(self, key):
        username = self.check_cookie('username')
        post = models.BlogPost.get_by_id(int(key))
        if username == post.username:
            self.render('editpost.html', post=post, username=username)
        else:
            self.redirect('/login')

    def post(self, key):
        username = self.check_cookie('username')
        post = models.BlogPost.get_by_id(int(key))
        if username == post.username:
            new_title = self.request.get('title')
            new_content = self.request.get('content')
            error = ""
            if new_title and new_content:
                post.title = new_title
                post.content = new_content
                post.put()  # Updating by calling put() with updated details
                self.redirect("/blog/" + str(post.key().id()))
            else:
                error = "Title and content cannot be left empty"
                self.render('editpost.html', post=post, error=error, 
                username=username)
        else:
            self.redirect('/login')

# Handles the addition of likes to a post
class LikePost(Handler):
    def get(self, key):
        username = self.check_cookie('username')
        user = db.GqlQuery("select * from User where username='%s'"
        % username).get()
        # User not being able to like his own post is handled in NewPost
        if not username:
            self.redirect('/login')
        elif key in user.postliked:
            self.redirect('/blog/'+key)
        else:
            post = models.BlogPost.get_by_id(int(key))
            post.likes = str(int(post.likes) + 1)
            post.put()
            user.postliked.append(key)
            user.put()
            self.redirect('/blog/'+key)

# Handles the addition of dislikes to a post
class DislikePost(Handler):
    def get(self, key):
        username = self.check_cookie('username')
        user = db.GqlQuery("select * from User where username='%s'"
        % username).get()
        if not username:
            self.redirect('/login')
        elif key in user.postliked:
            self.redirect('/blog/'+key)
        else:
            post = models.BlogPost.get_by_id(int(key))
            post.dislikes = str(int(post.dislikes) + 1)
            post.put()
            user.postliked.append(key)
            user.put()
            self.redirect('/blog/'+key)

# Handles adding a new Comment
class NewComment(Handler):
    def post(self):
        username = self.check_cookie('username')
        post_id = self.request.get('post_id')
        content = self.request.get('content')

        if not username:
            self.redirect('/login')
        else:
            c = models.Comment(username = username, post_id=post_id, content=content)
            c.put()
            self.redirect('/blog/'+post_id)

# Handles editing an existing Comment
class EditComment(Handler):
    def get(self, key, com_id):
        username = self.check_cookie('username')
        
        post = models.BlogPost.get_by_id(int(key))
        # Find comment that needs to be edited
        comment = models.Comment.get_by_id(int(com_id))

        if not username == comment.username:
            self.redirect('/blog/'+key)
        else:
            editcontent = comment.content
            # Delete the comment
            db.delete(comment.key())

            # Finding comments on the blog post
            comments = db.GqlQuery("select * from Comment where post_id='%s'"
            % key).run()

            self.render('post.html', post=post, username=username,
            comments=comments, editcontent=editcontent)

# Handles deleting an existing Comment
class DeleteComment(Handler):
    def get(self, com_id):
        username = self.check_cookie('username')
        # Find the comment
        comment = models.Comment.get_by_id(int(com_id))
        if not username == comment.username:
            self.redirect('/blog/'+key)
        else:
            # Save Post ID to redirect to
            post = comment.post_id
            # Delete the comment
            db.delete(comment.key())
            self.redirect('/blog/'+post)

# Handles creation of a new user
class Register(Handler):
    def get(self):
        self.render('register.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        error = []   # List with all the errors encountered

        # Validations for Username, Password and Email
        if not username or not re.match(r"^[a-zA-Z0-9_-]{3,20}$", username):
            error.append("The username entered is invalid")
        if not password or not re.match(r"^.{3,20}$", password):
            error.append("The password entered is invalid")
        if not password==verify:
            error.append("Passwords do not match")
        if not email or not re.match(r'^[\S]+@[\S]+\.[\S]+$', email):
            error.append("The email entered is invalid")

        # Check if username already exists
        exist = db.GqlQuery("select * from User where username='%s'"
        % username).get()
        if exist:
            error.append('Username already exists')

        if not error:
            # Creating a salt consisting of 5 letters
            salt = ""
            for i in range(0,5):
                salt = salt + random.choice('abcdefghijklmnopqrstuvwxyz')

            # Hashing the password and salt
            password = hashlib.sha256(password + salt).hexdigest() + ',' + salt

            # Add User to database
            user = models.User(username=username, password=password, verify=verify,
            email = email)
            user.put()

            # Create cookies
            self.create_cookie('user_id', user.key().id())
            self.create_cookie('username', user.username)

            self.redirect('/')
        else:
            self.render('register.html', username=username, password=password, 
                         verify=verify, email=email, error=error)

# Handles the login of existing user
class Login(Handler):
    def get(self):
        self.render('login.html')
    
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        error = []    # List with all the errors encountered
        if not username or not password:
            self.render('login.html', error='Please enter username and password')
        # Recover hashed password of User
        elif not db.GqlQuery("select * from User where username='%s'" % username).get():
            self.render('login.html', error='Username does not exist')
        else:    
            user = db.GqlQuery("select * from User where username='%s'" % username)
            salt = user[0].password.split(',')[1]
            new_pass = hashlib.sha256(password + salt).hexdigest() + ',' + salt

            if new_pass == user[0].password:
                # Create cookies
                self.create_cookie('user_id', user[0].key().id())
                self.create_cookie('username', username)

                self.redirect('/')
            else:
                self.render('login.html', error='Please enter correct password')

# Handles the logout of a user whose cookie is set
class Logout(Handler):
    def get(self):
        self.delete_cookie('user_id')
        self.delete_cookie('username')
        self.redirect('/')

# Handles the front page of the blog listing all the posts made
class MainPage(Handler):
    def get(self):
        username = self.check_cookie('username')
        posts = db.GqlQuery("select * from BlogPost order by created desc")
        self.render('index.html', posts=posts, username=username)
    
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/register', Register),
    ('/login', Login),
    ('/logout', Logout),
    ('/blog/([0-9]+)', Blog),
    ('/newpost', NewPost),
    ('/deletepost/([0-9]+)', DeletePost),
    ('/editpost/([0-9]+)', EditPost),
    ('/like/([0-9]+)', LikePost),
    ('/dislike/([0-9]+)', DislikePost),
    ('/newcomment', NewComment),
    ('/editcomment/([0-9]+)/([0-9]+)', EditComment),
    ('/deletecomment/([0-9]+)', DeleteComment)
], debug=True)
