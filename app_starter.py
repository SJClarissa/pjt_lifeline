# import libraries
from flask import Flask, render_template, request
from geo_boston import *
import numpy as np
import pandas as pd
from flask import Flask, request, Response, render_template



#loading yelp lifeline data
yelp = pd.read_csv('./data/final_yelp_scrape.csv', dtype={'zipcode': object})

#loading yelp lifeline frequency
lifeline_count = pd.read_csv('./data/zips_by_lifeline_count_loc_pop_zillow_1.4.csv',
                            dtype={'zipcode': object})
lifeline_count.drop("Unnamed: 0", axis =1, inplace = True)


#instantiate Flask app
app = Flask('__name__')

#instantiating class to save the zipcode entered by user in search box on p.1
class SaveZip:
    def __init__(self):
        self.my_zip = None

entered_zip = SaveZip()


@app.route("/")
@app.route("/send", methods=['GET', 'POST'])
def send():
    if request.method == 'POST':
        zip_detail = request.form['zipcode']

        #extraction population amount for the entered zipcode
        population_value = lifeline_count[lifeline_count['zipcode'] == zip_detail]['population']
        
        check_for_null = pd.isnull(population_value.values)
        if check_for_null:
            population = 'Is Not Available'
        else:
            # population=int(population_value.values[0])
            population=str("{:,}".format(round(population_value.values[0])))[:-2]
        #extracting mean home value for entered zipcode
        home_price_value = lifeline_count[lifeline_count.zipcode == zip_detail]['zillowprice']
        check_for_null_zillow = pd.isnull(home_price_value.values)
        if check_for_null_zillow:
            mean_home_price = 'Is Not Available'
        else:
            # mean_home_price = int(home_price_value.values[0])
            mean_home_price = str("{:,}".format(round(home_price_value.values[0])))[:-2]
        #extracting lifeline counts for entered zipcode

        safety = lifeline_count[lifeline_count['zipcode'] == zip_detail]['safe_sec'].values[0]

        food = lifeline_count[lifeline_count['zipcode'] == zip_detail]['food_water_shelter'].values[0]

        health = lifeline_count[lifeline_count['zipcode'] == zip_detail]['health_medical'].values[0]

        communications = lifeline_count[lifeline_count['zipcode'] == zip_detail]['communications'].values[0]

        transportation = lifeline_count[lifeline_count['zipcode'] == zip_detail]['transportation'].values[0]

        hazmat = lifeline_count[lifeline_count['zipcode'] == zip_detail]['hazmat'].values[0]

        energy = lifeline_count[lifeline_count['zipcode'] == zip_detail]['energy'].values[0]

        total_lifelines = lifeline_count[lifeline_count['zipcode'] == zip_detail]['total lifelines'].values[0]
        #saving the zip entered by user
        entered_zip.my_zip = zip_detail

        # zipcode = get_zipcode (zip_detail)
        map=map_one_zipcode(zip_detail)
        return render_template('zipcode.html', zipcode=zip_detail, map=map,
                                population=population,
                                mean_home_price=mean_home_price,
                                total_lifelines=total_lifelines,
                                safety=safety, food=food, health=health, communications=communications,
                                transportation=transportation, hazmat=hazmat, energy = energy)
    
    # Call main() function
    main() 
    if request.method == 'GET':
        print("here")
        return render_template('home.html')

    return render_template('home.html')

# #creating lifeline list page
@app.route('/lifelines')
def lifelines():

    # request.args: lifeline category as an input
    user_input2 = request.args
    print(*user_input2, sep = '\n')

    #convert entered lifeline by user to keyword in dataframe
    entered_lifeline = user_input2['lifeline'].lower()
    if entered_lifeline == 'safety and security':
        lifeline = 'safe_sec'
    if entered_lifeline == 'food water and shelter':
        lifeline = 'food_water_shelter'
    if entered_lifeline == 'health and medical':
        lifeline = 'health_medical'
    if entered_lifeline == 'energy':
        lifeline = 'energy'
    if entered_lifeline == 'communications':
        lifeline = 'communications'
    if entered_lifeline == 'transportation':
        lifeline = 'transportation'
    if entered_lifeline == 'hazardous material':
        lifeline = 'hazmat'


    print_to_screen=yelp[(yelp['zipcode']==entered_zip.my_zip)&(yelp['lifeline']==lifeline)]

    print_to_screen = print_to_screen[['name', 'display_address', 'city', 'state', 'zipcode', 'phone']]

    return render_template('lifelines.html',
                            lifeline = user_input2['lifeline'],
                            zipcode = entered_zip.my_zip,
                            tables=[print_to_screen.to_html(classes='data', header = True, index = False)])


if __name__ == "__main__":
    app.run(debug=True)
    # app.run(host='0.0.0.0')
    # app.run()