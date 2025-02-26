import csv
import re

def load_parks():
    '''
    Loading our National Park collection from a csv file and returning a dictionary that is ready to be uploaded into MongoDB
    The csv is sourced from https://www.kaggle.com/datasets/thedevastator/the-united-states-national-parks/data which is  licensed as public 
    The data on whether each park has an entrance fee comes from https://www.nps.gov/aboutus/entrance-fee-prices.htm?park=&state=&entrancePassRequired=&timedEntry=&page=1&parking=
    Park images found from https://www.nps.gov/media/multimedia-search.htm#sort=score+desc&q= 
    For future reference the associated images for each park are stored in the static/images folder with the name being park_name.
    '''
    src = 'static/db/national_parks.csv'
    file = csv.reader(open(src,'r'))
    headers = next(file)
    headers = [headers[1], headers[3],headers[5], headers[7],headers[8]]
    parks = [[l[1], l[3],l[5], l[7],l[8]] for l in file]

    db_parks = []

    for p in parks: #loading a json style object that then can be put into mongoDB once thats set up 
        p_name, p_state, p_size, desc, fee = p
        state = re.match('([a-zA-Z\s.&]*?)[\d]', p_state)[1]

        if '&' in state:
            state = state.replace('&', ', ')
        if '*' in p_name:
            p_name = p_name.replace('*', '')

        p_name = p_name.strip()
        p_img = p_name.replace('.','').replace(' ','')+'.jpg'

        park = {'park_name':p_name,
                'state':state,
                'size': p_size,
                'entrance_fee': bool(fee),
                'img_src':p_img}
        
        db_parks.append(park)
    return db_parks

if __name__ == "__main__":
    load_parks()