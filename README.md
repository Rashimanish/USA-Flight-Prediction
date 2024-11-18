# Machine Learning-Flask-Web-App 

This is a web application designed to show the project structure for a machine learning model deployed using flask. 
This project features a machine learning model that has been trained to detect whether or not a flight will be delayed or not and the duration
## Technology used
- Python
- Machine Learning - CatBoost & LightGBM
- Pandas
- Numpy
- Scikit-learn
- Flask
- HTML
- CSS
- Pymongo


In order to predict whether a flight is delayed or on time you can deploy this application locally and submit queries to the machine learning model to recieve predictions through a simple user interface. 

The model was trained using the
Dataset for binary classification & multiple classification ([see here](https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr)). This project emphasizes more the development process of creating deploy-friendly machine learning projects, rather than the creating of the predictive model itself.



## Installation

#Option 1:~
Use the Pre-built Executable:
~~~bash
After downloading the project , navigate to the `dist` directory where `Flightapp.exe` is located,  Double-click on `Flightapp.exe` to start the application.
~~~

#Option 2:
Clone the git hub repo locally.
~~~bash
git clone https://github.com/Rashimanish/-FlightPrediction.git
~~~


Create a new virtual environment in the project directory.
~~~bash
python3 -m venv ./venv
~~~

Activate the virtual environment.
~~~bash
source venv/bin/activate
~~~

While in the virtual environment, install required dependencies from `requirements.txt`.

~~~bash
pip install -r ./requirements.txt
~~~

Now we can deploy the web application via
~~~bash
python app.py
~~~

and navigate to `http://127.0.0.1:5000/` to see it live. On this page, a user can then submit the form and receive predictions from the trained model and determine if the Flight will be delayed or not and the expected duration of the delay. 


The application may then be terminated with the following commands.
~~~bash
$ ^C           # exit flask application (ctrl-c)
$ deactivate   # exit virtual environment
~~~
