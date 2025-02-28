#!/usr/bin/env python3
import os
import datetime
import db as parkData
from flask import Flask, render_template, request, redirect, url_for
import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv, dotenv_values
import logging

load_dotenv()  # load environment variables from .env file

def create_app():
    """
    Create and configure the Flask application.
    returns: app: the Flask application object
    # """
    app = Flask(__name__)
    # load flask config from env variables
    config = dotenv_values()
    app.config.from_mapping(config)

    # Set up logging in Docker container's output
    logging.basicConfig(level=logging.DEBUG)
    
    cxn = pymongo.MongoClient(os.getenv("MONGO_URI"))
    db = cxn[os.getenv("MONGO_DBNAME")]

    try:
        cxn.admin.command("ping")
        print(" *", "Connected to MongoDB!")
    except Exception as e:
        print(" * MongoDB connection error:", e)

    # Drop all collections to prevent duplicated data getting 
    # inserted into the database whenever the app is restarted
    collections = db.list_collection_names()
    for collection in collections:
        db[collection].drop()

    # Load park data into the database
    data = parkData.load_parks()
    app.logger.debug("create_app(): data: %s", data)
    national_parks = db["national_parks"]
    result = national_parks.insert_many(data)

    @app.route("/", methods=["GET", "POST"])
    def index():
        """
        Route for the home page, which is the login page.
        """
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            # Authentication logic
            if username and password:
                app.logger.debug("* index(): Authenticating user: %s", username)
                doc = db.users.find_one({"username": username})
                if doc:
                    if doc["password"] == password:
                        app.logger.debug("* index(): User authenticated: %s", username)
                        return redirect(url_for("visited", user_id=doc["_id"]))  # Redirect if login successful
                    else:
                        return render_template("index.html", error="Failed to login: Invalid credentials")
                else:
                    return render_template("index.html", error="Failed to login: User not found. Please create a new user account")  # Show error

        return render_template("index.html")  # Show login page (GET request)

    @app.route("/create-new-user")
    def createNewUser():
        """
        Route for the New User Registration page.
        """
        return render_template("create_new_user.html")
    
    @app.route("/add-new-user", methods=["POST"])
    def addNewUser():
        """
        Route for adding a new user to the database.
        """
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        confirm_password = request.form.get("confirmPassword").strip()
        app.logger.debug("*addNewUser(): username: %s, password: %s, confirm_password: %s", username, password, confirm_password)
        
        # Example authentication logic
        if username and password and confirm_password:
            if password == confirm_password:
                # Add new user to the database
                doc = {
                    "username": username,
                    "password": password,
                    "created_at": datetime.datetime.utcnow(),
                }
                newUser = db.users.insert_one(doc)
                newUserId = newUser.inserted_id
                app.logger.debug("*addNewUser(): newUser: %s", newUser)
                app.logger.debug("*addNewUser(): newUserId: %s", newUserId)  
                # Redirect to the visited_parks page
                return render_template("my_parks_visited.html", user_id=newUserId, is_new_user="true")
            else:
                return render_template("create_new_user.html", error="Failed to add new user: Passwords do not match")
        else:
            return render_template("create_new_user.html", error="Failed to add new user: Missing required fields")

    @app.route("/search")
    def search():
        """
        Route for the search page.
        Returns:
            rendered template (str): The rendered HTML template.
        """

        return render_template("search.html", title="Search")
    
    @app.route("/discover")
    def discover():
        """
        Route for the discover page.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        return render_template("discover.html", title="Discover")
    
    @app.route("/visited/<user_id>")
    def visited(user_id):
        """
        Route for the visited parks page.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        app.logger.debug("* visited(): user_id: %s", user_id)
        visited_docs = list(db.user_parks.find({"user_id": user_id, "visited": "true"}).sort("created_at", -1))
        if (visited_docs == []):
            app.logger.debug("* visited(): No visited parks found for user_id: %s", user_id)
        else:
            for vdoc in visited_docs:
                park_doc = db.national_parks.find_one({"_id": ObjectId(vdoc["park_id"])})
                app.logger.debug("* addVisitedPark(): Found park_doc: %s", park_doc)
                vdoc["park_name"] = park_doc["park_name"]
                vdoc["state"] = park_doc["state"]
                vdoc["img_src"] = park_doc["img_src"]
                app.logger.debug("* addVisitedPark(): Enriched visited_park_doc: %s", vdoc)
            app.logger.debug("* addVisitedPark(): Found visited park docs: %s", visited_docs)

        # Redirect to the visited_parks page with all of user's visited parks
        return render_template("my_parks_visited.html", user_id=user_id, is_new_user="false", docs=visited_docs)
    
    
    # @app.route("/liked")
    # def liked():
    #     """
    #     Route for the liked parks page.
    #     Returns:
    #         rendered template (str): The rendered HTML template.
    #     """
    #     return render_template("my_parks_liked.html")
    
    @app.route("/add-park/<user_id>")
    def addPark(user_id):
        """
        Route for the initial search page of adding a visited park.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        return render_template("add_visited_park.html", user_id=user_id)
    
    @app.route("/search-visited-park/<user_id>", methods=["POST"])
    def searchVisitedPark(user_id):
        """
        Route for searching for a visited park to add.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        app.logger.debug("* searchVisitedPark(): request.form: %s", request.form)
        app.logger.debug("* searchVisitedPark(): user_id: %s", user_id)
        
        search_input = request.form.get("searchInput", "").strip()
        search_type = request.form.get("searchType", "").strip()

        docs = []
        if search_input:  # Only search if input is provided
            if search_type == "by_name":
                app.logger.debug("* searchVisitedPark(): search by name: %s", search_input)
                docs = list(db.national_parks.find({"park_name": {"$regex": search_input, "$options": "i"}}))
            elif search_type == "by_state":
                app.logger.debug("* searchVisitedPark(): search by state: %s", search_input)
                docs = list(db.national_parks.find({"state": {"$regex": search_input, "$options": "i"}}))

        if docs:
            app.logger.debug("* searchVisitedPark(): Found documents: %s", docs)
        else:
            app.logger.debug("* searchVisitedPark(): No documents found")

        return render_template("visited_park_search_result.html", user_id=user_id, docs=docs)


    @app.route("/add-visited-park/<user_id>/<park_id>")
    def addVisitedPark(user_id, park_id):
        """
        Route for adding a user visited park to the database.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        if not user_id or not park_id:
            return render_template("error.html", error="Failed to add visited park: Missing required fields")
        
        app.logger.debug("* addVisitedPark(): user_id: %s, park_id: %s", user_id, park_id)

        # Check if there is an existing user_visited_park record for this user and park
        # User might have liked the park before, but not visited it
        doc = db.user_parks.find_one({"user_id": user_id, "park_id": park_id})
        if doc:
            if (doc.get("visited") != "true"):
                app.logger.debug("* addVisitedPark(): Found 1 doc: %s", doc)
                db.user_parks.update_one({"_id": ObjectId(doc["_id"])},
                                         {"$set": {"visited": "true"}})   
                app.logger.debug("* addVisitedPark(): Updated this doc")
            else:
                # Don't do anything if the user has already visited the park
                app.logger.debug("* addVisitedPark(): Error - Found 1 doc but already visited: %s", doc)
        else:
            # Add a new user_visited_park record to the database
            doc = {
                "user_id": user_id,
                "park_id": park_id,
                "visited": "true",
                "rating": "Not rated",
                "comment": "",
                "liked": "false",
                "created_at": datetime.datetime.utcnow(),
            }
            newdoc = db.user_parks.insert_one(doc)
            app.logger.debug("* addVisitedPark(): Inserted 1 doc: %s", newdoc.inserted_id)

        return redirect(url_for("visited", user_id=user_id))
    
    
    @app.route("/edit/<user_id>/<park_id>")
    def edit(user_id, park_id):
        """
        Route for displaying a form for user to modify comment, rating, like status
        of a park that the user has visited.
        Returns:
            redirect (Response): A redirect response to the my_parks_visited page.
        """
        app.logger.debug("* edit(): user_id: %s, park_id: %s", user_id, park_id)

        user_doc = db.user_parks.find_one({"user_id": user_id, "park_id": park_id})
        app.logger.debug("* edit(): user_doc: %s", user_doc)
        
        park_doc = db.national_parks.find_one({"_id": ObjectId(park_id)})
        app.logger.debug("* edit(): park_doc: %s", park_doc)
        user_doc["park_name"] = park_doc["park_name"]
        user_doc["state"] = park_doc["state"]
        user_doc["img_src"] = park_doc["img_src"]
        app.logger.debug("* edit(): Enriched user_doc: %s", user_doc)
        return render_template("edit.html", user_id=user_id, park_id=park_id, doc=user_doc)
    
    @app.route("/edit-visited-park/<user_id>/<park_id>", methods=["POST"])
    def editVisitedPark(user_id, park_id):
        """
        Route updating a user_visited_park record in the database.
        Returns:
            redirect (Response): A redirect response to the my_parks_visited page.
        """
        if not user_id or not park_id:
            return render_template("error.html", error="Failed to edit visited park: Missing required fields")
        
        app.logger.debug("* editVisitedPark(): user_id: %s, park_id: %s", user_id, park_id)

        user_rating = request.form.get("rating", "").strip()
        user_liked = request.form.get("liked", "").strip()
        user_comment = request.form.get("comment", "").strip()
        app.logger.debug("* editVisitedPark(): user_rating: %s, user_liked: %s, user_comment: %s", user_rating, user_liked, user_comment)

        if user_liked == "Yes":
            user_liked = "true"
        else:
            user_liked = "false"

        # Find the existing user_visited_park record for this user and park
        doc = db.user_parks.find_one({"user_id": user_id, "park_id": park_id})
        if doc:
            app.logger.debug("* addVisitedPark(): Found 1 doc: %s", doc)
            db.user_parks.update_one({"_id": ObjectId(doc["_id"])},
                                     {"$set": {"rating": user_rating,
                                                "comment": user_comment,
                                                "liked": user_liked,
                                                "created_at": datetime.datetime.utcnow()}})   
            app.logger.debug("* editVisitedPark(): Updated this doc")
        else:
            app.logger.debug("* editVisitedPark(): Odd, no doc found for this user and park, insert new one")
            # Should NOT happen, but just in case - Add a new user_visited_park record to the database
            doc = {
                "user_id": user_id,
                "park_id": park_id,
                "visited": "true",
                "rating": user_rating,
                "comment": user_comment,
                "liked": user_liked,
                "created_at": datetime.datetime.utcnow(),
            }
            newdoc = db.user_parks.insert_one(doc)
            app.logger.debug("* editVisitedPark(): Inserted 1 doc: %s", newdoc.inserted_id)

        return redirect(url_for("visited", user_id=user_id))

    @app.route("/delete/<user_id>/<park_id>")
    def delete(user_id, park_id):
        """
        Route for GET requests to the delete page.
        Deletes the specified record from the database, and then redirects the browser to the home page.
        Args:
            park_id (str): The ID of the park rating id to delete.
        Returns:
            redirect (Response): A redirect response to the home page.
        """
        db.user_parks.delete_one({"user_id": user_id, "park_id": park_id})
        return redirect(url_for("visited", user_id=user_id))
    
    @app.route("/park/<park_id>")
    def park(park_id):
        
        return render_template("index.html")
    
    @app.route("/my-parks/park-information/<park_id>")
    def park_info(park_id):
        """
        Route for GET requests to the park information page.
        Displays a list of information about the park and a link to add it to their visited page
        Args:
            park_id (str): The ID of the park rating it to edit.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        doc = national_parks.find_one({"_id": ObjectId(park_id)})
        app.logger.debug("* parkInformation(): Found park_doc: %s", doc)
        # user_input = db.uservisited.find({'park_id': park_id})
        # doc['rating']= 4.2
        # doc['like'] = 100
        # doc['comment'] = 'commentingggg'
        # for d in user_input:
        #     doc['rating'] += d['rating']
        #     doc['like'] += 1 if d['liked'] else 0
        #     doc['comment'].append(d['comment'])
        # doc['rating'] /= len(user_input)
        return render_template("park_information.html", docs = doc)
    
    @app.errorhandler(Exception)
    def handle_error(e):
        """
        Output any errors - good for debugging.
        Args:
            e (Exception): The exception object.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        return render_template("error.html", error=e)
    return app

app = create_app()

if __name__ == "__main__":
    FLASK_PORT = os.getenv("FLASK_PORT", "5000")
    FLASK_ENV = os.getenv("FLASK_ENV")
    print(f"FLASK_ENV: {FLASK_ENV}, FLASK_PORT: {FLASK_PORT}")

    app.run(debug=True, port=FLASK_PORT)


'''
import datetime
from flask import Flask, render_template, request, redirect, url_for
import pymongo
from dotenv import load_dotenv, dotenv_values

load_dotenv()  # load environment variables from .env file


def create_app():
    """
    Create and configure the Flask application.
    returns: app: the Flask application object
    """

    app = Flask(__name__)
    # load flask config from env variables
    config = dotenv_values()
    app.config.from_mapping(config)

    cxn = pymongo.MongoClient(os.getenv("MONGO_URI"))
    db = cxn[os.getenv("MONGO_DBNAME")]

    try:
        cxn.admin.command("ping")
        print(" *", "Connected to MongoDB!")
    except Exception as e:
        print(" * MongoDB connection error:", e)

    @app.route("/")
    def home():
        """
        Route for the home page.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        docs = db.messages.find({}).sort("created_at", -1)
        return render_template("index.html", docs=docs)

    @app.route("/create", methods=["POST"])
    def create_post():
        """
        Route for POST requests to the create page.
        Accepts the form submission data for a new document and saves the document to the database.
        Returns:
            redirect (Response): A redirect response to the home page.
        """
        name = request.form["fname"]
        message = request.form["fmessage"]

        doc = {
            "name": name,
            "message": message,
            "created_at": datetime.datetime.utcnow(),
        }
        db.messages.insert_one(doc)

        return redirect(url_for("home"))

    @app.route("/edit/<post_id>")
    def edit(post_id):
        """
        Route for GET requests to the edit page.
        Displays a form users can fill out to edit an existing record.
        Args:
            post_id (str): The ID of the post to edit.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        doc = db.messages.find_one({"_id": ObjectId(post_id)})
        return render_template("edit.html", doc=doc)

    @app.route("/edit/<post_id>", methods=["POST"])
    def edit_post(post_id):
        """
        Route for POST requests to the edit page.
        Accepts the form submission data for the specified document and updates the document in the database.
        Args:
            post_id (str): The ID of the post to edit.
        Returns:
            redirect (Response): A redirect response to the home page.
        """
        name = request.form["fname"]
        message = request.form["fmessage"]

        doc = {
            "name": name,
            "message": message,
            "created_at": datetime.datetime.utcnow(),
        }

        db.messages.update_one({"_id": ObjectId(post_id)}, {"$set": doc})

        return redirect(url_for("home"))

    @app.route("/delete/<post_id>")
    def delete(post_id):
        """
        Route for GET requests to the delete page.
        Deletes the specified record from the database, and then redirects the browser to the home page.
        Args:
            post_id (str): The ID of the post to delete.
        Returns:
            redirect (Response): A redirect response to the home page.
        """
        db.messages.delete_one({"_id": ObjectId(post_id)})
        return redirect(url_for("home"))

    @app.route("/delete-by-content/<post_name>/<post_message>", methods=["POST"])
    def delete_by_content(post_name, post_message):
        """
        Route for POST requests to delete all post by their author's name and post message.
        Deletes the specified record from the database, and then redirects the browser to the home page.
        Args:
            post_name (str): The name of the author of the post.
            post_message (str): The contents of the message of the post.
        Returns:
            redirect (Response): A redirect response to the home page.
        """
        db.messages.delete_many({"name": post_name, "message": post_message})
        return redirect(url_for("home"))
'''