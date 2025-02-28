import csv
import re
import datetime

def clean_size(size_string):
    km_part = size_string.split("(")
    return km_part[1].split()[0].replace(",", "")

def load_parks():
    '''
    Loading our National Park collection from a csv file and returning a dictionary that is ready to be uploaded into MongoDB
    The csv is sourced from https://www.kaggle.com/datasets/thedevastator/the-united-states-national-parks/data which is  licensed as public 
    The data on whether each park has an entrance fee comes from https://www.nps.gov/aboutus/entrance-fee-prices.htm?park=&state=&entrancePassRequired=&timedEntry=&page=1&parking=
    Park images found from https://www.nps.gov/media/multimedia-search.htm#sort=score+desc&q= 
    For future reference the associated images for each park are stored in the static/images folder with the name being park_name.
    '''
    src = 'static/db/national_parks.csv'
    db_parks = []
    try:
        with open(src, "r") as src_file:
            file = csv.reader(src_file)
            headers = next(file)
            headers = [headers[1], headers[3],headers[5], headers[7],headers[8]]
            parks = [[l[1], l[3],l[5], l[7],l[8]] for l in file]

            for p in parks: #loading a json style object that then can be put into mongoDB once thats set up 
                p_name, p_state, p_size, desc, fee = p
                state = re.match('([a-zA-Z\s.&]*?)[\d]', p_state)[1]

                if '&' in state:
                    state = state.replace('&', ', ')
                if '*' in p_name:
                    p_name = p_name.replace('*', '')

                p_name = p_name.strip()
                p_img = 'images/parks/'+p_name.replace('.','').replace(' ','')+'.jpg'
                p_size = clean_size(p_size)

                park = {'park_name':p_name,
                        'state':state,
                        'size': float(p_size),
                        'entrance_fee': bool(fee),
                        'description': desc,
                        'img_src':p_img}
                
                db_parks.append(park)
    except FileNotFoundError:
        print("Error: File not found.")
    except PermissionError:
        print("Error: Permission denied.")
    except IOError:
        print("Error: An I/O error occurred.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return db_parks

def generate_test_users():
    user = ['test1', 'test2', 'test3', 'test4', 'test5']
    pwd = ['helloworld', 'password', '12345678', 'softwareeng', 'nationalparks']
    return [{'username': u, 'password': p,"created_at": datetime.datetime.utcnow()} for u,p in zip(user,pwd)]

def generate_test_visited(users,parks):
    '''{
            _id: ObjectId('67c1f4bc4ee22593c868addc'),
            user_id: '67c1f4b74ee22593c868addb',
            park_id: '67c1f4aa85e2e604261ecddd',
            visited: 'true',
            rating: 'Not rated',
            comment: '',
            liked: 'false',
            created_at: ISODate('2025-02-28T17:39:08.798Z')
    }'''
    uidx =   [0, 0,1, 1, 1,2,2, 3,4, 4, 4, 4]
    pidx =   [0,20,3,15,3,0,60,5,20,60,60,0]
    ratings = [5, 3,4, 2,3,2, 4,5, 3, 5, 2,3]
    liked = [True, False, False, True, True, False, False, True, True, True, False, True]
    comments = ['so fun', 'beautiful', 'great!','too warm', 'enjoyed it','so fun', 'too warm', 'beautiful', 'great!', 'could have been better', 'amazing park', 'i had so much fun!']
    
    visited_docs = []
    for v in range(len(comments)):
        visited_docs.append({
            'user_id': users[uidx[v]]['_id'],
            'park_id': parks[pidx[v]]['_id'],
            'visited': 'true',
            'rating':ratings[v],
            'comment':comments[v],
            'liked': liked[v],
            "created_at": datetime.datetime.utcnow()
        })

    return visited_docs



if __name__ == "__main__":
    db = load_parks()
    print(db)


    users = generate_test_users()
    print(users)

    print(generate_test_visited(parks=db,users=users))