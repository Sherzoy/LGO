from flask import Flask, request, jsonify
import subprocess
import openai
import sys
import utils
import json
from flask_cors import CORS
import re
from bardapi import Bard
import numpy as np
import pandas as pd

app = Flask(__name__)
CORS(app, origins='http://localhost:3000', allow_headers=["Content-Type"])


def get_config_key():
    with open('../config.json') as f:
        config_data = json.load(f)
    return config_data["api_key"]

openai.api_key = get_config_key()

def add_cors_headers(response):
    # Allow requests from the specific origin (your React app's origin)
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    # Allow the Content-Type header for the preflight request
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/chatbot', methods=['POST', 'OPTIONS'])
def run_chatbot():
    if request.method == 'OPTIONS':
        response = jsonify({})
    else:
        data = request.get_json()
        user_message = data.get('message')

        # Run the Python script (example: my_script.py) with user_message as an argument
        result = get_response(user_message)
        print(result)
        json_res = json.loads(result)
        print(json_res)
        entry_ass = json_res['entry_ass']
        is_ass = json_res['is_ass']

        res = calculate_lbo(entry_ass, is_ass)
        response = jsonify({'message': res})

    response = add_cors_headers(response)
    return response


def get_response(code):
    message = [{"role": "system", "content" : "You are supposed to take prompts and digest it into a json file without doing any mathematical processing of the data. We needed entry assumptions in the format as follows entry_ass = { 'entry_multiple' , 'Rev_Y1': ,     'EBITDA_Y1_Margin': , 'debt_ratio':  , 'equity_ratio': , 'years':} and income assumptions in the format as follows is_ass={ 'rev_growth':  , 'int_rate':  , 'tax_rate': , 'capex_per_of_rev': , 'change_in_NWC': , 'depreciation':} put all percentages as decimals and all numbers as their actual values. Calculate debt ratio as initial debt divided by purchase value. Equity ratio is (1-debt ratio). The capex per of rev should be a decimal less than 1. The rev growth should be a decimal less than 1.\nKnowledge cutoff: 2021-09-01\nCurrent date: 2023-03-02"},
                {"role": "user", "content" : code}]
    completion = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = message,
    )
    return completion.choices[0].message["content"]



def calculate_lbo(entry_ass, is_ass):
    if entry_ass['Rev_Y1'] / 1000000 == 0:
        entry_ass['Rev_Y1'] *= 1000000
    
    if is_ass['change_in_NWC'] / 1000000 == 0:
        is_ass['change_in_NWC'] *= 1000000

    if is_ass['depreciation'] / 1000000 == 0:
        is_ass['depreciation'] *= 1000000

    entry_ass['EBITDA_Y1']=entry_ass['Rev_Y1']*entry_ass['EBITDA_Y1_Margin']
    entry_ass["price_paid"]=entry_ass["entry_multiple"]*entry_ass["EBITDA_Y1"]  

    entry_ass["debt_portion"]=entry_ass['debt_ratio']*entry_ass['price_paid']
    entry_ass['equity_portion']=entry_ass['equity_ratio']*entry_ass['price_paid']

    years=[i for i in range(1, entry_ass['years']+2)]
    rows=["Rev","EBITDA","less: D&A","EBIT", "less: Interest","EBT", "less: Taxes","Earnings"]
    lbo_is = pd.DataFrame(data=None,index=rows,columns=years)

    lbo_is[1].loc['Rev']=entry_ass['Rev_Y1']
    i = 2
    while i <= len(lbo_is.loc['Rev']):
        lbo_is[i].loc['Rev']=lbo_is[(i-1)].loc['Rev']*(1+is_ass['rev_growth'])
        i+=1
    
    lbo_is.loc['EBITDA']=lbo_is.loc['Rev']*entry_ass['EBITDA_Y1_Margin']

    lbo_is.loc['less: D&A']= -is_ass['depreciation']

    lbo_is.loc['EBIT']=lbo_is.loc['EBITDA']+lbo_is.loc['less: D&A']

    lbo_is.loc['less: Interest']=-is_ass['int_rate']*entry_ass['debt_portion']

    lbo_is.loc['EBT']=lbo_is.loc['EBIT']+lbo_is.loc['less: Interest']

    lbo_is.loc['less: Taxes']=lbo_is.loc['EBT']*-is_ass['tax_rate']

    lbo_is.loc['Earnings']=lbo_is.loc['EBT']+lbo_is.loc['less: Taxes']

    lbo_fcf=pd.DataFrame(data=None, index=["Earnings", "plus: D&A", "less: capex", "less: NWC", "FCF"], columns=years)

    lbo_fcf.loc['Earnings']=lbo_is.loc['Earnings']
    lbo_fcf.loc['plus: D&A']=-lbo_is.loc['less: D&A']
    lbo_fcf.loc['less: capex']=lbo_is.loc['Rev']*-is_ass["capex_per_of_rev"]
    lbo_fcf.loc['less: NWC']=-is_ass['change_in_NWC']
    lbo_fcf.loc['FCF']=lbo_fcf.loc[['Earnings','plus: D&A','less: capex', 'less: NWC']].sum()

    year_list = years[:-1]
    cumulative_fcf=lbo_fcf[[1,2,3,4,5]].loc['FCF'].sum()

    exit_returns={
    "exit_EBITDA":lbo_is[entry_ass['years']+1].loc['EBITDA'],
    'exit_multiple':entry_ass['entry_multiple'],
    'beginning_debt':entry_ass['debt_portion'],
    'cumulative_FCF':cumulative_fcf,
    }

    exit_returns['exit_TEV']= exit_returns['exit_EBITDA']*exit_returns['exit_multiple']
    exit_returns['ending_debt']= exit_returns['beginning_debt']-exit_returns['cumulative_FCF']  
    exit_returns['ending_equity']=exit_returns['exit_TEV']-exit_returns['ending_debt']
    exit_returns['MOIC']=exit_returns['ending_equity']/entry_ass['equity_portion']

    return exit_returns


if __name__ == '__main__':
    app.run(debug=True)
