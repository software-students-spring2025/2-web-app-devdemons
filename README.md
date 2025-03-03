# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

Park Passport is an application that allows users to explore and share their experiences at US National Parks while keeping track of the parks they have visited. 

## User stories

1. As a traveler, I want to be able to sign up for the application so that I can see other people's national park information.

2. As a traveler, I want to be able to log into my own account so that I can see where all my national park destinations are stored.

3. As a traveler, I want to have an organized list of national parks so I can explore new national parks.

4. As a traveler, I want to keep track of all of the national parks I have been to so that I can plan better for future travels.

5. As a traveler, I want to upload reviews of my experience at the national parks so that I can share my experience with others.

6. As a traveler, I want to be able to see whether national parks are free or have an entry fee so that I can plan ahead and budget.

7. As a traveler, I want to be able to see generally how many reviews other users have posted so that I can know how much they've traveled and use that to interpret their reviews.

8. As a traveler, I want to be able to see other user's opinions about a national park in one easy place so that I can learn its rating and their comments

9. As a traveler, I want to be able to see information about a national park in one easy place so that I can learn where they are, its size, and see a photo to decide if I want to visit

10. As a traveler, I want to see popular national parks so that I can find new places to visit.

11. As a traveler, I want to be able to search through a list of recommended national parks and filter by my specific needs so that I can see where other people are visiting.

12. As a traveler I want to be able to search through National parks and get matching results so that I can find a place I want to visit

[Issues pages](https://github.com/software-students-spring2025/2-web-app-devdemons/issues)

## Steps necessary to run the software

See instructions. Delete this line and place instructions to download, configure, and run the software here.

Two files are necessary to load our app and be able to run it. First, create your own .env file. Included in our repository is an env.example file. Most of the lines are filled in, but you must put a MongoDB database name and uri in the  firsttwo lines. You also must create a Flask Login secret key to place in the last line. Once the .env file is set up, you have to go and fill out a few lines in the docker-compose.yml file to match. You must make sure the ports math up and fill in the MongoDb environment variables to match what is in your .env file. under services -> flask-app -> environment change MONGO_DBNAME and MONGO_URI to your own links and then under mongodb -> environment change the MONGO_INITDB_ROOT_USERNAME and MONGO_INITDB_ROOT_PASSWORD to the correct values for you. From there you should be ready to run the flask app.

In the terminal type docker compose up --force-recreate --build and then go to the correct address according to the ports you set up. You should then be seeing our login page and can create an account and go through our app. 






## Task boards

[Sprint 1](https://github.com/orgs/software-students-spring2025/projects/27/views/1)
[Sprint 2](https://github.com/orgs/software-students-spring2025/projects/72/views/1?filterQuery=)