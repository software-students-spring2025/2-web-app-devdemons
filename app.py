#!/usr/bin/env python3
import os
import datetime
import db as parkData
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user, logout_user
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

    # set up for flask login
    app.secret_key = os.getenv("KEY")
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "index"

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
    pdata = parkData.load_parks()
    app.logger.debug("create_app(): data: %s", pdata)
    national_parks = db["national_parks"]
    result = national_parks.insert_many(pdata)    
    
    # Load user data into the database
    udata = parkData.generate_test_users()
    app.logger.debug("create_app(): users: %s", udata)
    result = db.users.insert_many(udata)

    vdata = parkData.generate_test_visited(users=db.users.find(), parks=national_parks.find())
    app.logger.debug("create_app(): visited: %s", vdata)  
    result = db.user_parks.insert_many(vdata)

    # class for user login
    class User(UserMixin):
        pass
    
    @login_manager.user_loader
    def user_loader(id):
        user_file = db.users.find_one({"_id": ObjectId(id)})
        if not user_file:
            return None
        user = User()
        user.id = str(user_file["_id"])
        user.username = user_file['username']
        return user

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
                        user = User()
                        user.id = str(doc["_id"])
                        user.username = doc["username"]
                        login_user(user)
                        return redirect(url_for("visited"))  # Redirect if login successful
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
                user_doc = db.users.find_one({"_id": newUserId})
                user = User()
                user.id = str(doc["_id"])
                user.username = doc["username"]
                login_user(user)
                # Redirect to the visited_parks page
                return redirect(url_for("visited"))
            else:
                return render_template("create_new_user.html", error="Failed to add new user: Passwords do not match")
        else:
            return render_template("create_new_user.html", error="Failed to add new user: Missing required fields")
    
    @app.route("/logout")
    @login_required
    def logout():
        """
        Route for logging user out
        """
        logout_user()
        return redirect(url_for("index"))

    @app.route("/search")
    @login_required
    def search():
        """
        Route for the search page.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        return render_template("search.html")
    

    def findParksByRequest(request):
        docs = []

        search_input = request.form.get("searchInput", "").strip()
        search_type = request.form.get("searchType", "").strip()

        if search_input:  # Only search if input is provided
            if search_type == "by_name":
                app.logger.debug("* findParksByRequest(): search by name: %s", search_input)
                docs = list(db.national_parks.find({"park_name": {"$regex": search_input, "$options": "i"}}))
            elif search_type == "by_state":
                app.logger.debug("* findParksByRequest(): search by state: %s", search_input)
                docs = list(db.national_parks.find({"state": {"$regex": search_input, "$options": "i"}}))

        return docs
    

    @app.route("/find-parks", methods=["POST"])
    @login_required
    def findParks():
        """
        Route for searching for any parks.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        docs = findParksByRequest(request)

        if docs:
            app.logger.debug("* findParks(): Found documents: %s", docs)
        else:
            app.logger.debug("* findParks(): No documents found")

        return render_template("find_parks_search_result.html", docs=docs, user_id = current_user.id)
    

    @app.route("/discover")
    @login_required
    def discover():
        """
        Route for the discover page.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        app.logger.debug("* discover(): Route accessed")

        # filter for parks that have been liked and group by the park id to get total like count
        top_liked = list(db.user_parks.aggregate([
            {"$match": {"liked": "true"}},
            {"$group": {"_id": "$park_id", "num_likes": {"$sum": 1}}},
            {"$sort": {"num_likes": -1}},
            {"$limit": 5}
        ]))
        app.logger.debug("* discover(): Found most liked parks: %s", top_liked)

        # add missing fields to top liked parks
        for park in top_liked:
            park_doc = db.national_parks.find_one({"_id": ObjectId(park["_id"])})
            park["park_name"] = park_doc["park_name"]
            park["state"] = park_doc["state"]
        app.logger.debug("* discover(): added fields to top liked parks: %s", top_liked)

        # filter for parks that are top rated and group by average rating
        top_rated = list(db.user_parks.aggregate([
            {"$match": {"rating": {"$ne": "Not Rated"}}},
            {"$group": {"_id": "$park_id", "avg_rating": {"$avg": {"$convert": {"input": "$rating", "to": "double"}}}}},
            {"$sort": {"avg_rating": -1}},
            {"$limit": 5}
        ]))
        app.logger.debug("* discover(): Found top rated parks: %s", top_rated)

        # add missing fields to top rated parks
        for park in top_rated:
            park_doc = db.national_parks.find_one({"_id": ObjectId(park["_id"])})
            park["park_name"] = park_doc["park_name"]
            park["state"] = park_doc["state"]
        app.logger.debug("* discover(): added fields to top rated parks: %s", top_rated)

        # filter parks by largest
        largest_parks = list(db.national_parks.find().sort("size", -1).limit(5))
        app.logger.debug("* discover(): found largest parks")

        return render_template("discover.html", title="Discover", top_liked_parks = top_liked, top_rated_parks = top_rated, largest_parks = largest_parks)
    
    @app.route("/visited")
    @login_required
    def visited():
        """
        Route for displaying my_visited_parks page.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        user_id = current_user.id
        app.logger.debug("* visited(): user_id: %s", user_id)
        visited_docs = list(db.user_parks.find({"user_id": ObjectId(user_id), "visited": "true"}).sort("created_at", -1))
        if (visited_docs == []):
            app.logger.debug("* visited(): No visited parks found for user_id: %s", user_id)
        else:
            for vdoc in visited_docs:
                park_doc = db.national_parks.find_one({"_id": ObjectId(vdoc["park_id"])})
                app.logger.debug("* visited(): Found park_doc: %s", park_doc)
                vdoc["park_name"] = park_doc["park_name"]
                vdoc["state"] = park_doc["state"]
                vdoc["img_src"] = park_doc["img_src"]
                app.logger.debug("* visited(): Enriched visited_park_doc: %s", vdoc)
            app.logger.debug("* visited(): Found visited park docs: %s", visited_docs)

        # Redirect to my_visited_parks page with all parks the user has visited
        return render_template("my_parks_visited.html", user_id=user_id, is_new_user="false", docs=visited_docs)
    
    
    @app.route("/add-park")
    @login_required
    def addPark():
        """
        Route for the initial search page of adding a visited park.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        return render_template("add_visited_park.html")
    
    @app.route("/search-visited-park", methods=["POST"])
    @login_required
    def searchVisitedPark():
        """
        Route for searching for a visited park to add.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        app.logger.debug("* searchVisitedPark(): request.form: %s", request.form)
        app.logger.debug("* searchVisitedPark(): user_id: %s", current_user.id)
        
        docs = findParksByRequest(request)
        
        if docs:
            app.logger.debug("* searchVisitedPark(): Found documents: %s", docs)
        else:
            app.logger.debug("* searchVisitedPark(): No documents found")

        return render_template("visited_park_search_result.html", docs=docs, user_id = current_user.id)


    @app.route("/add-visited-park/<park_id>")
    @login_required
    def addVisitedPark(park_id):
        """
        Route for adding a user visited park to the database.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        user_id = current_user.id
        if not user_id or not park_id:
            return render_template("error.html", error="Failed to add visited park: Missing required fields")
        
        app.logger.debug("* addVisitedPark(): user_id: %s, park_id: %s", user_id, park_id)

        # Check if there is an existing user_visited_park record for this user and park
        # User might have liked the park before, but not visited it
        doc = db.user_parks.find_one({"user_id": ObjectId(user_id), "park_id": ObjectId(park_id)})
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
                "user_id": ObjectId(user_id),
                "park_id": ObjectId(park_id),
                "visited": "true",
                "rating": "Not Rated",
                "comment": "",
                "liked": "false",
                "created_at": datetime.datetime.utcnow(),
            }
            newdoc = db.user_parks.insert_one(doc)
            app.logger.debug("* addVisitedPark(): Inserted 1 doc: %s", newdoc.inserted_id)

        return redirect(url_for("visited"))
    
    
    @app.route("/edit/<park_id>")
    @login_required
    def edit(park_id):
        """
        Route for displaying a form for user to modify comment, rating, like status
        of a park that the user has visited.
        Returns:
            redirect (Response): A redirect response to the my_parks_visited page.
        """
        user_id = current_user.id
        app.logger.debug("* edit(): user_id: %s, park_id: %s", user_id, park_id)

        user_doc = db.user_parks.find_one({"user_id": ObjectId(user_id), "park_id": ObjectId(park_id)})
        app.logger.debug("* edit(): user_doc: %s", user_doc)
        
        park_doc = db.national_parks.find_one({"_id": ObjectId(park_id)})
        app.logger.debug("* edit(): park_doc: %s", park_doc)
        user_doc["park_name"] = park_doc["park_name"]
        user_doc["state"] = park_doc["state"]
        user_doc["img_src"] = park_doc["img_src"]
        app.logger.debug("* edit(): Enriched user_doc: %s", user_doc)
        return render_template("edit.html", park_id=park_id, doc=user_doc)
    
    @app.route("/edit-visited-park/<park_id>", methods=["POST"])
    @login_required
    def editVisitedPark(park_id):
        """
        Route updating a user_visited_park record in the database.
        Returns:
            redirect (Response): A redirect response to the my_parks_visited page.
        """
        user_id = current_user.id
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
        doc = db.user_parks.find_one({"user_id": ObjectId(user_id), "park_id": ObjectId(park_id)})
        if doc:
            app.logger.debug("* addVisitedPark(): Found 1 doc: %s", doc)
            db.user_parks.update_one({"_id": ObjectId(doc["_id"])},
                                     {"$set": {"rating": int(user_rating) if user_rating else 'Not Rated',
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
                "rating": int(user_rating),
                "comment": user_comment,
                "liked": user_liked,
                "created_at": datetime.datetime.utcnow(),
            }
            newdoc = db.user_parks.insert_one(doc)
            app.logger.debug("* editVisitedPark(): Inserted 1 doc: %s", newdoc.inserted_id)

        return redirect(url_for("visited"))

    @app.route("/delete/<park_id>")
    @login_required
    def delete(park_id):
        """
        Route for GET requests to the delete page.
        Deletes the specified record from the database, and then redirects the browser to the home page.
        Args:
            park_id (str): The ID of the park rating id to delete.
        Returns:
            redirect (Response): A redirect response to the home page.
        """
        user_id = current_user.id
        db.user_parks.delete_one({"user_id": ObjectId(user_id), "park_id": ObjectId(park_id)})
        return redirect(url_for("visited"))
    
    @app.route("/park/<park_id>")
    @login_required
    def park(park_id):
        
        return redirect(url_for("park_info", park_id = park_id))
    

    @app.route("/my-parks/park-information/<park_id>")
    @login_required
    def park_info(park_id):
        """
        Route for GET requests to the park information page.
        Displays a list of information about the park and a link to add it to their visited page
        Args:
            park_id (str): The ID of the park rating it to edit.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        doc = db.national_parks.find_one({"_id": ObjectId(park_id)})
        if doc is None:
            return render_template("error.html", error="Failed to find park: incorrect park_id")

        app.logger.debug("* parkInformation(): Found park_doc: %s", doc)
        user_input = list(db.user_parks.find({'park_id': ObjectId(park_id)}, {'user_id':1,'comment': 1, 'liked': 1, 'rating': 1}))
        app.logger.debug("* parkInformation(): Found user_park docs: %s", user_input)

        doc['comments'] = []
        doc['likes'] = 0
        doc['rating'] = 0

        if user_input is not None:
            mean = 0
            ct = len(user_input)

            for u in user_input:
                username = db.users.find_one({"_id": ObjectId(u['user_id'])})
                if u['comment'] != '':
                    doc['comments'].append(f"{username['username']}: {u['comment']}")
                if u['liked'] == 'true':
                    doc['likes'] += 1
                if u['rating'] != 'Not Rated':
                    mean += int(u['rating'])

            # Avoid division by zero
            m = mean / ct if ct > 0 else 0
            doc['rating'] = f'{m:.2f}'

            app.logger.debug("* parkInformation(): Compiled user info: %s", doc)

        return render_template("park_information.html", docs=doc)


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