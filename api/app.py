# Importing essential libraries and modules
import sys
import os
# Get the current directory of your script
current_directory = os.path.dirname(os.path.abspath(__file__))
# Add the 'utils' directory to the Python path
utils_directory = os.path.join(current_directory, 'utils')
sys.path.append(utils_directory)
from flask import Flask, render_template, request, Markup
import numpy as np
import pandas as pd
from fertilizer import fertilizer_dic
import requests
import config
import pickle
import joblib
from sklearn.ensemble import RandomForestClassifier
from flask import Flask,request, render_template
import numpy as np
import pickle
import sklearn
print(sklearn.__version__)
#loading models
dtr = pickle.load(open('dtr.pkl','rb'))
preprocessor = pickle.load(open('preprocessor1.pkl','rb'))



# Loading crop recommendation model
#crop_recommendation_model = RandomForestClassifier()
crop_recommendation_model_path = 'models/DecisionTree.pkl'

crop_recommendation_model = pickle.load(
    open(crop_recommendation_model_path, 'rb'))
#crop_recommendation_model = joblib.load(crop_recommendation_model_path)
#joblib.dump(crop_recommendation_model, crop_recommendation_model_path)
# Custom functions for calculations


def weather_fetch(city_name):
    """
    Fetch and returns the temperature and humidity of a city
    :params: city_name
    :return: temperature, humidity
    """
    api_key = config.weather_api_key
    base_url = "http://api.openweathermap.org/data/2.5/weather?"

    complete_url = base_url + "appid=" + api_key + "&q=" + city_name
    response = requests.get(complete_url)
    x = response.json()

    if x["cod"] != "404":
        y = x["main"]

        temperature = round((y["temp"] - 273.15), 2)
        humidity = y["humidity"]
        return temperature, humidity
    else:
        return None




# ===============================================================================================
# ------------------------------------ FLASK APP -------------------------------------------------


app = Flask(__name__)

# render home page


@ app.route('/')
def home():
    title = 'Harvestify - Home'
    return render_template('index.html', title=title)

# render crop recommendation form page


@ app.route('/crop-recommend')
def crop_recommend():
    title = 'Harvestify - Crop Recommendation'
    return render_template('crop.html', title=title)

# render fertilizer recommendation form page


@ app.route('/fertilizer')
def fertilizer_recommendation():
    title = 'Harvestify - Fertilizer Suggestion'

    return render_template('fertilizer.html', title=title)

# render disease prediction input page




# ===============================================================================================

# RENDER PREDICTION PAGES

# render crop recommendation result page


@ app.route('/crop-predict', methods=['POST'])
def crop_prediction():
    title = 'Harvestify - Crop Recommendation'

    if request.method == 'POST':
        try:
            N = int(request.form['nitrogen'])
            P = int(request.form['phosphorous'])
            K = int(request.form['pottasium'])
            ph = float(request.form['ph'])
            rainfall = float(request.form['rainfall'])

        # state = request.form.get("stt")
            city = request.form.get("city")

            if weather_fetch(city) != None:
                temperature, humidity = weather_fetch(city)
                data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
                my_prediction = crop_recommendation_model.predict(data)
                final_prediction = my_prediction[0]

                return render_template('crop-result.html', prediction=final_prediction, title=title)

            else:

                return render_template('try_again.html', title=title)

        except Exception as e:
            return f"An error occurred: {str(e)}"
    else:
        return "Invalid request method"
# render fertilizer recommendation result page


@ app.route('/fertilizer-predict', methods=['POST'])
def fert_recommend():
    title = 'Harvestify - Fertilizer Suggestion'

    crop_name = str(request.form['cropname'])
    N = int(request.form['nitrogen'])
    P = int(request.form['phosphorous'])
    K = int(request.form['pottasium'])
    # ph = float(request.form['ph'])

    df = pd.read_csv('Data/fertilizer.csv')

    nr = df[df['Crop'] == crop_name]['N'].iloc[0]
    pr = df[df['Crop'] == crop_name]['P'].iloc[0]
    kr = df[df['Crop'] == crop_name]['K'].iloc[0]

    n = nr - N
    p = pr - P
    k = kr - K
    temp = {abs(n): "N", abs(p): "P", abs(k): "K"}
    max_value = temp[max(temp.keys())]
    if max_value == "N":
        if n < 0:
            key = 'NHigh'
        else:
            key = "Nlow"
    elif max_value == "P":
        if p < 0:
            key = 'PHigh'
        else:
            key = "Plow"
    else:
        if k < 0:
            key = 'KHigh'
        else:
            key = "Klow"

    response = Markup(str(fertilizer_dic[key]))

    return render_template('fertilizer-result.html', recommendation=response, title=title)

@app.route('/yieldhome',methods=['POST','GET'])
def index():
    return render_template('yieldindex.html')
@app.route("/yieldpredict",methods=['POST','GET'])
def predict():
    if request.method == 'POST':
        Year = request.form['Year']
        average_rain_fall_mm_per_year = request.form['average_rain_fall_mm_per_year']
        pesticides_tonnes = request.form['pesticides_tonnes']
        avg_temp = request.form['avg_temp']
        Area = request.form['Area']
        Item  = request.form['Item']

        features = np.array([[Year,average_rain_fall_mm_per_year,pesticides_tonnes,avg_temp,Area,Item]],dtype=object)
        transformed_features = preprocessor.transform(features)
        prediction = dtr.predict(transformed_features).reshape(1,-1)

        return render_template('yieldindex.html', prediction=prediction)





# ===============================================================================================
if __name__ == '__main__':
    app.run(debug=True)
