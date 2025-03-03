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

1. Clone our git repository to your local machine. You can use this URL: `https://github.com/software-students-spring2025/2-web-app-devdemons.git`

2. Find the .env and docker-compose.yml files sent by my team member in the class discord under the channel [team-devdemons](https://discord.com/channels/1198812317274615830/1342293481808199750)

   - Copy these files into the local version of your repository

3. Bring up a terminal window and type in the following command: `docker compose up --force-recreate --build`

   - If you get a message saying the port is in use you can change the port in the .env and docker compose files

4. Go to [http://127.0.0.1:10000/](http://127.0.0.1:10000/) (or to the correct port if you changed it)

5. You have now successfully loaded our app! You can create an account, add parks to your list, and explore. Or you can login using one of these pre-existing accounts with the following username and password:

   Account 1

   - Username: test1
   - Password: helloworld

   Account 2

   - Username: test2
   - Password: password

   The above test user accounts are preloaded with park ratings, likes, and user comments into the database at startup. To view these comments you could look at the pages for parks like Yellowstone or Acadia to see how users' comments and ratings are displayed publicly.

6. If you edit anything while the site is running it will not appear. To load all changes, open a new terminal window and type `docker compose down` and then redo step 3 in the other terminal window.
   - Any information you added to the db will be lost each time the site is rebuilt and launched.

## Task boards

[Sprint 1](https://github.com/orgs/software-students-spring2025/projects/27/views/1) \
[Sprint 2](https://github.com/orgs/software-students-spring2025/projects/72/views/1?filterQuery=)
