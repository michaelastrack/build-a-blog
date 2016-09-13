#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
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
#
import webapp2
import jinja2
import os

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment (loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def get_posts (limit, offset):
    lim = int (limit)
    off = int (offset)
    getentries = db.GqlQuery("SELECT * FROM Entry ORDER BY created DESC Limit %s Offset %s" % (lim, off))

    return getentries

class Handler (webapp2.RequestHandler):
    def write (self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str (self, template, **params):
        t = jinja_env.get_template(template)
        return t.render (params)

    def render (self, template, **kw):
        self.write (self.render_str(template, **kw))

class Entry (db.Model):
    title = db.StringProperty (required = True)
    body = db.TextProperty (required = True)
    created = db.DateTimeProperty (auto_now_add = True)

# Handler for entering new posts

class NewHandler(Handler):
    def post(self):
        title = self.request.get("title")
        body = self.request.get("body")

        if title and body:
            a = Entry (title = title, body = body)
            a.put()
            Newid = str(a.key().id())
            self.redirect("/blog/" + Newid)
        else:
            error = "We need both a title and a post!"
            self.render_newpost(title, body, error)

    def render_newpost(self, title="", body="", error=""):
        self.render("newpost.html", title=title, body=body, error=error)

    def get(self):
        self.render_newpost()

# Handler for the main blog page

class BlogHandler(Handler):
    def render_blog(self):
        page = self.request.get("page")
        error = ""

        # Set page to one if no page number was entered by the user
        if not page:
            page = 1

        # Determine the total number of entries in the database and the page number of the last page
        page_size = 5
        entries = db.GqlQuery("SELECT * FROM Entry ORDER BY created DESC")
        fullcount = entries.count (offset = 0, limit = 1000)

        lastpage = fullcount // page_size + 1
        if fullcount % page_size == 0:
            page = page - 1

        # If the user enters a non number for a page number display an error
        page = str(page)
        if not page.isdigit():
            page = 1
            error = "That's not a valid page number"

        # if the user enters a page number that is larger than the last page number display an error
        page = int(page)
        if page > lastpage:
            page = lastpage
            error = "This is the last page"

        # Determine whether or not the page needs a previous page link
        if page == 1:
            p = False
        else:
            p = True

        offset = (page) * 5

        shortentries = get_posts(5, (page -1)*5)
        nextentries = get_posts(5, page * 5)

        # Determine whether a page needs a next page link
        if (nextentries.count(offset = offset, limit = page_size)) > 1:
            n = True
        else:
            n = False

        self.render("blog.html", entries=shortentries, page = page, n = n, p = p, error = error)

    def get(self):
        self.render_blog()

    def post(self):
        self.render_blog()

# Handler for viewing individual posts

class ViewPostHandler(Handler):
    def render_view(self, title = "", body= ""):
        self.render("viewpost.html", title = title, body = body)


    def get (self, id):

        entry = Entry.get_by_id(int (id), parent=None)
        title = entry.title
        body = entry.body

        if title and body:
            self.render_view(title = title, body = body)






app = webapp2.WSGIApplication([
    ('/', BlogHandler), ("/newpost", NewHandler), ("/blog", BlogHandler),
    webapp2.Route("/blog/<id:\d+>", ViewPostHandler)
], debug=True)
