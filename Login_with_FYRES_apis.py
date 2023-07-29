import time
from flask import Flask, request, jsonify
from fyers_api import accessToken
from pyotp import TOTP
from selenium import webdriver

app = Flask(__name__)
#Here an endpoint /geberate_authcode is defined which is a GET request having paramaters client_id, secret_key, redirect_url, response_type and state,all these are re
#required to get Fyre url to authenticate that the user is valid user ,on successful run of this API it return an endpoint url whrere user need to enter client_id and 6 digits
# otp to get auth code
@app.route('/generate_authcode', methods=['GET'])
def generate_authcode():
    try:
        # Get parameters from the request args
        client_id = request.args.get('client_id')
        secret_key = request.args.get('secret_key')
        redirect_uri = request.args.get('redirect_uri')
        response_type = request.args.get('response_type')
        state = request.args.get('state')

        # Create a session model with the given parameters
        session = accessToken.SessionModel(
            client_id=client_id,
            secret_key=secret_key,
            redirect_uri=redirect_uri,
            response_type=response_type
        )

        # Generate the auth code
        response = session.generate_authcode()

        return jsonify({"Fyre_url_to_get_auth_code": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#once u have the authcode generated successfully after the generate_authcode call 
#this api can be called with authcode to generate token for making further requests
@app.route('/generate_token', methods=['POST'])
def generate_token():
    try:
        # Get parameters from the request
        client_id = request.json.get('client_id')
        secret_key = request.json.get('secret_key')
        redirect_uri = request.json.get('redirect_uri')
        response_type = request.json.get('response_type')
        grant_type = request.json.get('grant_type')
        auth_code = request.json.get('auth_code')

        # Create a session model with the given parameters
        session = accessToken.SessionModel(
            client_id=client_id,
            secret_key=secret_key,
            redirect_uri=redirect_uri,
            response_type=response_type,
            grant_type=grant_type
        )

        # Set the token using the provided auth_code
        session.set_token(auth_code)

        # Generate the access_token and refresh_token
        response = session.generate_token()

        return jsonify({"access_token": response['access_token']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate_token_automate', methods=['POST'])
def generate_token_automate():
    try:
        client_id = request.args.get('client_id')
        secret_key = request.args.get('secret_key')
        redirect_uri = request.args.get('redirect_uri')
        response_type = request.args.get('response_type')
        state = request.args.get('state')
        #fetch pin
        pin_1=request.args.get('p0')
        pin_2=request.args.get('p1')
        pin_3=request.args.get('p2')
        pin_4=request.args.get('p3')
        # Create a session model with the given parameters
        session = accessToken.SessionModel(
            client_id=client_id,
            secret_key=secret_key,
            redirect_uri=redirect_uri,
            response_type=response_type
        )

        # Generate the auth code
        response = session.generate_authcode()

        driver=webdriver.Chrome()
        #open the chrome tab and get the FYRE endpont to validate user
        driver.get(response)
        time.sleep(10)
        #automate the filling of client id and click submit button
        driver.find_element_by_xpath('//*[@id="fy_client_id"]').send_keys(client_id)
        driver.find_element_by_xpath('//*[@id="clientIdSubmit"]').click()
        time.sleep(10)
        #get the 6 digit pin which gets generated using TOTP class of totp library
        t=TOTP(totp).now()
        #entering the 6 digits so far obtained
        driver.find_element_by_xpath('//*[@id="first"]').send_keys(t[0])
        driver.find_element_by_xpath('//*[@id="first"]').send_keys(t[1])
        driver.find_element_by_xpath('//*[@id="first"]').send_keys(t[2])
        driver.find_element_by_xpath('//*[@id="first"]').send_keys(t[3])
        driver.find_element_by_xpath('//*[@id="first"]').send_keys(t[4])
        driver.find_element_by_xpath('//*[@id="first"]').send_keys(t[5])
        driver.find_element_by_xpath('//*[@id="ConfirmOtpSubmit"]').click()
        time.sleep(10)
        #entering the pin setted by user 
        driver.find_element_by_id("verify_pin_page").find_element_by_id("first").send_keys(pin_1)
        driver.find_element_by_id("verify_pin_page").find_element_by_id("first").send_keys(pin_2)
        driver.find_element_by_id("verify_pin_page").find_element_by_id("first").send_keys(pin_3)
        driver.find_element_by_id("verify_pin_page").find_element_by_id("first").send_keys(pin_4)
        driver.find_element_by_xpath('//*[@id="verifyPinSubmit"]').click()
        #on successful validate ,get the current redirectedd url with authcode attached 
        current_url=driver.current_url
        #fetch the auth code from current utl
        auth_code=current_url[current_url.index('auth_code=')+10:current_url.index('&state')]
        driver.quit()
        session = accessToken.SessionModel(
            client_id=client_id,
            secret_key=secret_key,
            redirect_uri=redirect_uri,
            response_type=response_type,
            grant_type="authorization_code"
        )

        # Set the token using the provided auth_code
        
        session.set_token(auth_code)

        # Generate the access_token and refresh_token
        response = session.generate_token()

        return jsonify({"access_token": response['access_token']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
