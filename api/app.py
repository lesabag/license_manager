import os
import requests
import logging
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

AUTO_DOMAIN = 'luc-automation.liveu-rnd.com:8543'
STG_DOMAIN = 'luc-staging.liveu.tv:443'

get_token_url = 'https://{}/luc/luc-core-web/rest/login/j_oauth_token_grant'
get_list_of_service_url = 'https://{}/luc/luc-core-web/rest/v2/admin/units' \
                          '/Boss100_lu300_393131343164346565366133353436/services'
api_base_url = "https://{}/luc/luc-core-web/rest/billing/{}/{}/services/{}"

global access_token, res
global env_user, env_password, radio_name, lic_name, selected_env
label_text = ""


@app.route('/')
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    UI_username = request.form.get('username')
    os.environ['LUC_USERNAME'] = UI_username
    UI_password = request.form.get('password')
    os.environ['LUC_USERNAME'] = UI_password

    if 'AUTO' in request.form.get('listbox'):
        setEnvironment(AUTO_DOMAIN)
    else:
        setEnvironment(STG_DOMAIN)

    setUserAndPassword(UI_username, UI_password)

    tokenRes = getToken(get_username(), get_password())
    print(f'res = {tokenRes}')
    set_acc_token(tokenRes)
    if not tokenRes:
        print('No access_token generated!, registration failed')
        app.logger.error('No access_token generated!, registration failed')
    else:
        return redirect(url_for('index', username=UI_username, password=UI_password))

    return "Registration failed"


def add_license_request(url):
    global label_text

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'  # Adjust the content type if needed
    }
    req_response = requests.post(url, headers=headers)
    if req_response.status_code == 204:
        print("ADD request successful sent")
        setLabelText(f'ADD {url.split("/")[-1].upper()}')
    else:
        label_text = 'ADD request failed with http error:' + str(req_response.status_code)


def remove_license_request(url):
    global label_text

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    req_response = requests.delete(url, headers=headers)
    if req_response.status_code == 204:
        print("REMOVE request successful sent")
        setLabelText(f'REMOVE {url.split("/")[-1].upper()}')
    else:
        label_text = 'REMOVE request failed with http error:' + str(req_response.status_code)


@app.route('/index', methods=['GET', 'POST'])
def index():
    global label_text, radio_name, lic_name

    lu_text = request.form.get('lutext', "")
    mmh_text = request.form.get('mmhtext', "")

    action = request.form.get('action')
    if action:
        radio_name = request.form.get('radio')
        if radio_name:
            lic_name = radio_name.split("_")[-1].lower()
            license_request_by_action(action, radio_name, lic_name,lu_text, mmh_text)
        else:
            label_text = 'You need to select any license..'
    return render_template('index.html', label_text=label_text, lu_text=lu_text, mmh_text=mmh_text)


def license_request_by_action(action, radio_selection, license_name, lu_text, mmh_text):
    global label_text
    print(f' action: {action}, radio: {radio_selection}, license: {license_name},'
          f' lutext: {lu_text}, mmh_text: {mmh_text}')

    if 'LU' in radio_selection:
        if action == 'add' and lu_text:
            add_license_request(api_base_url.format(getEnvironment(), "units", lu_text, license_name))
        elif action == 'remove' and lu_text:
            remove_license_request(api_base_url.format(getEnvironment(), "units", lu_text, license_name))
        else:
            label_text = 'you need to provide LU S/N'

    if 'LU' not in radio_selection:
        if action == 'add' and mmh_text:
            add_license_request(api_base_url.format(getEnvironment(), "servers", lu_text, license_name))
        elif action == 'remove' and mmh_text:
            remove_license_request(api_base_url.format(getEnvironment(), "servers", lu_text, license_name))
        else:
            label_text = 'you need to provide MMH S/N'


def setLabelText(licenseName):
    global label_text
    label_text = licenseName + ' license operation ended successfully!'


def set_acc_token(token):
    global res
    res = token


def setEnvironment(env):
    global selected_env
    selected_env = env


def getEnvironment():
    return selected_env

def setUserAndPassword(user, password):
    global env_user, env_password
    env_user = user
    env_password = password

def get_username():
    return env_user


def get_password():
    return env_password



def get_access_token():
    return access_token


# Setter function
def set_access_token(token):
    global access_token
    access_token = token


def getToken(username, password):
    global label_text, res
    print(f'get_token_url.format(getEnvironment(): {get_token_url.format(getEnvironment())}')
    res = requests.post(get_token_url.format(getEnvironment()), auth=(username, password))

    if res.status_code == 200:
        label_text = 'REGISTRATION ENDED SUCCESSFULLY'
        json_data = res.json()
        access_token = json_data.get('access_token')

        if access_token:
            print("Access Token:", access_token)
            set_access_token(access_token)
            return True
        else:
            return False
    else:
        label_text = 'REGISTRATION FAILED'


if __name__ == '__main__':
    app.run(debug=True)
