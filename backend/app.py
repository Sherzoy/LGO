from flask import Flask, request, jsonify
import subprocess
import openai
import sys
import utils
import json
from flask_cors import CORS
import re
from bardapi import Bard

app = Flask(__name__)
CORS(app, origins='http://localhost:3000', allow_headers=["Content-Type"])


def get_bard_key():
    with open('../config.json') as f:
        config_data = json.load(f)
    return config_data["bard_api_key"]

bard = Bard(token=get_bard_key())

def add_cors_headers(response):
    # Allow requests from the specific origin (your React app's origin)
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    # Allow the Content-Type header for the preflight request
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route('/api/bard', methods=['POST', 'OPTIONS'])
def run_bard():
    if request.method == 'OPTIONS':
        response = jsonify({})
    
    else:
        data = request.get_json()
        user_message = data.get('message')

        result = bard.get_answer("You are taking a paper LBO model test, where accuracy is essential. Your only goal is to give a series of steps to calculate the MOIC (Multiple on invested capital) that is extremely accurate. For each step, explain your reasoning. Here are the steps: 1. Sources and uses: First, calculate the enterprise value. Second, calculate the debt and equity financing split. 2. Projecting leveered cash flow: Calculate EBITDA first. Derive net income. Project levered free cash flow. 3. Calculate MOIC and IRR. Here is the scenario: " + user_message)['content']

        response = jsonify({'message': result})
    
    response = add_cors_headers(response)
    return response




if __name__ == '__main__':
    app.run(debug=True)