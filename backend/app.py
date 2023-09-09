from flask import Flask, request, jsonify, send_file, make_response
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
import io
import os
import tempfile
from io import StringIO

app = Flask(__name__)
CORS(app, origins='http://localhost:3000', allow_headers=["Content-Type"])

current_json = {}

#read the text in prompt.txt as the string prompt
with open('prompt.txt', 'r') as file:
    prompt = file.read()

#read the text in prompt.txt as the string prompt
with open('excelprompt.txt', 'r') as file:
    excelprompt = file.read()

#prompt = "1. Task: Create the following JSON file without mathematical processing of the data. 2. JSON Structure: The JSON file should have two sections: entry assumptions as 'entry_ass' and income assumptions as 'is_ass'. 3. Formulas: Refer to the following formulas for calculating values: - 'equity_ratio' = (1-debt_ratio) - 'debt_ratio' = initial debt divded by the purchase value 4. 'entry_ass': This section should contain the following fields: - 'entry_multiple': The transaction multiple for the entry assumption. - 'Rev_Y1': Revenue in Year 1, represented as '100 million' and converted to '100000000'. - 'EBITDA_Y1_Margin': EBITDA margin in Year 1 as a decimal (e.g., 0.15 for 15%). - 'debt_ratio': To be calculated as initial debt divided by the purchase value. - 'equity_ratio': To be calculated as (1 - debt_ratio). - 'years': The number of years for the investment horizon. 5. 'is_ass': This section should contain the following fields: - 'rev_growth': Revenue growth rate as a decimal (e.g., 0.05 for 5%). - 'int_rate': Interest rate for senior secured debt as a decimal (e.g., 0.04 for 4%). - 'tax_rate': Tax rate as a decimal (e.g., 0.3 for 30%). - 'capex_per_of_rev': Capital expenditures as a percentage of revenue as a decimal (e.g., 0.04 for 4%). - 'change_in_NWC': Annual change in net working capital, represented as '2 million' and converted to '2000000' - 'depreciation': Annual depreciation amount, represented as '3 million' and converted to '3000000'. 6. Representation: Represent all percentages as decimals and all numbers as their actual values (not in word form like 'million'). 7. Number Representation: Read the numbers as '100 million' and represent them as '100000000' in the JSON."

def read_text_to_excel(text):
    output_file = 'out.xlsx'
    # Split the text into rows based on newline characters
    rows = text.strip().split('\n')

    data = [row.split('|') for row in rows]

    # Create a DataFrame from the data
    df = pd.DataFrame(data)

    # Save the DataFrame to an Excel file
    df.to_excel(output_file, index=False)
    return df

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
    global current_json
    if request.method == 'OPTIONS':
        response = jsonify({})
    else:
        data = request.get_json()
        user_message = data.get('message')

        # Run the Python script (example: my_script.py) with user_message as an argument
        result = get_response(user_message)
        current_json = json.loads(result)
        response = jsonify({'message': result, 'excel': 'hello'})

    response = add_cors_headers(response)
    return response

@app.route('/api/submit', methods=['POST', 'OPTIONS'])
def calculate():
    if request.method == 'OPTIONS':
        response = jsonify({})
    else:
        global current_json
        data = request.get_json()
        entry_ass_new = data.get("entry_ass")
        is_ass_new = data.get("is_ass")
        print(current_json)
        for key in entry_ass_new:
            if entry_ass_new[key] != current_json["entry_ass"][key]:
                current_json["entry_ass"][key] = entry_ass_new[key]
        for key in is_ass_new:
            if is_ass_new[key] != current_json["is_ass"][key]:
                current_json["is_ass"][key] = is_ass_new[key]
        print(current_json)
        result = calculate_lbo(data.get("entry_ass"), data.get("is_ass"))
        response = jsonify({'message': result})

    response = add_cors_headers(response)
    return response

@app.route('/api/exportToExcel', methods=['GET'])
def export_to_excel():
    if request.method == 'GET':

        
        # Process jsondata and convert it to an Excel file (DataFrame)
        #exceltext = makeExcel(current_json)
        #df = read_text_to_excel(exceltext)
        # Save the DataFrame to an Excel file (BytesIO buffer)
        csv_string = makeExcel()
        excel_file_path = os.path.join(tempfile.gettempdir(), 'generated_excel.xlsx')
        to_excel(csv_string,excel_file_path)
        #df.to_excel(excel_file_path, index=False)
    

        # Return the Excel file as a downloadable response
        response = make_response(send_file(excel_file_path, as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = add_cors_headers(response)
        return response

def get_response(code):
    message = [{"role": "system", "content" : prompt + "\nKnowledge cutoff: 2021-09-01\nCurrent date: 2023-03-02"},
                {"role": "user", "content" : code}]
    completion = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = message,
    )
    return completion.choices[0].message["content"]

def makeExcel():

    entry_ass = current_json["entry_ass"]
    is_ass = current_json["is_ass"]
    years = entry_ass.get("years", "")
    years = int(years)

    csv_rows = []
    csv_rows.append("entry_multiple" + "," + str(entry_ass.get("entry_multiple", "")) + "," * years)
    csv_rows.append("Rev_Y1" + "," + str(entry_ass.get("Rev_Y1", "")) + "," * years)
    csv_rows.append("EBITDA_Y1_Margin" + "," + str(entry_ass.get("EBITDA_Y1_Margin", "")) + "," * years)
    csv_rows.append("debt_ratio" + "," + str(entry_ass.get("debt_ratio", "")) + "," * years)
    csv_rows.append("equity_ratio" + "," + str(entry_ass.get("equity_ratio", "")) + "," * years)
    csv_rows.append("years" + "," + str(entry_ass.get("years", "")) + "," * years)
    csv_rows.append("rev_growth" + "," + str(is_ass.get("rev_growth", "")) + "," * years)
    csv_rows.append("int_rate" + "," + str(is_ass.get("int_rate", "")) + "," * years)
    csv_rows.append("tax_rate" + "," + str(is_ass.get("tax_rate", "")) + "," * years)
    csv_rows.append("capex_per_of_rev" + "," + str(is_ass.get("capex_per_of_rev", "")) + "," * years)
    csv_rows.append("change_in_NWC" + "," + str(is_ass.get("change_in_NWC", "")) + "," * years)
    csv_rows.append("depreciation" + "," + str(is_ass.get("depreciation", "")) + "," * years)
    
    csv_rows.append(","*(years+1))
    csv_rows.append(","*(years+1))
    
    excel_rows = [
        "EBITDA Y1,=$B$3*$B$2" + "," * years,
        "price_paid,=$B$1*$B$15" + "," * years,
        "debt_portion,=$B$4*$B$16" + "," * years,
        "equity_portion,=$B$5*$B$16" + "," * years
    ]

    csv_rows.extend(excel_rows)


    csv_rows.append(","*(years+1))
    csv_rows.append(","*(years+1))


    # Generate Years row
    years_row = "Year," + ",".join(str(year) for year in range(1, years + 2))
    csv_rows.append(years_row)

    # Generate Rev expressions
    rev_row = "Rev," + ",".join("=$B$2" if i == 0 else "={}22*(1+$B$7)".format(chr(65 + i)) for i in range(years+1))
    csv_rows.append(rev_row)

    ebitda_row = "EBITDA," + ",".join("={}22*$B$3".format(chr(66 + i)) for i in range(years+1))
    csv_rows.append(ebitda_row)

    less_da_row = "less: D&A" + ",=-$B$12" * (years+1)
    ebit_row = "EBIT," + ",".join("={}23+{}24".format(chr(66 + i), chr(66 + i)) for i in range(years+1))
    less_interest_row = "less: Interest" + ",=-$B$8*$B$17" * (years+1)
    ebt_row = "EBT," + ",".join("={}25+{}26".format(chr(66 + i), chr(66 + i)) for i in range(years+1))
    less_taxes_row = "less: Taxes," + ",".join("={}27*-$B$9".format(chr(66 + i)) for i in range(years+1))
    earnings_row = "Earnings," + ",".join("={}27+{}28".format(chr(66 + i), chr(66 + i)) for i in range(years)) + ","
    plus_da_row = "plus: D&A," + ",".join("=-{}24".format(chr(66 + i)) for i in range(years))+","
    less_capex_row = "less: capex," + ",".join("={}22*-$B$10".format(chr(66 + i)) for i in range(years))+","
    less_nwc_row = "less: NWC" + ",=-$B$11" * (years)+","
    fcf_row = "FCF," + ",".join("=SUM({}29:{}32)".format(chr(66 + i), chr(66 + i)) for i in range(years))+","
    csv_rows.append(less_da_row)
    csv_rows.append(ebit_row)
    csv_rows.append(less_interest_row)
    csv_rows.append(ebt_row)
    csv_rows.append(less_taxes_row)
    csv_rows.append(earnings_row)
    csv_rows.append(plus_da_row)
    csv_rows.append(less_capex_row)
    csv_rows.append(less_nwc_row)
    csv_rows.append(fcf_row)

    csv_rows.append(","*(years+1))
    csv_rows.append(","*(years+1))

    exit_EBGITDA_row = "exit_EBITDA,"+ "=${}$23".format(chr(66 + years))+","*years
    exit_multiple_row = "exit_multiple,=$B$1"+ ","*years
    beggining_debt_row = "beggining_debt,=$B$17"+ ","*years
    cumulative_FCF_row = "cumulative_FCF,=SUM(B33:{}33)".format(chr(66 + years-1))+","*years
    csv_rows.append(exit_EBGITDA_row)
    csv_rows.append(exit_multiple_row)
    csv_rows.append(beggining_debt_row)
    csv_rows.append(cumulative_FCF_row)

    csv_rows.append(","*(years+1))
    csv_rows.append(","*(years+1))

    exit_TEV_row = "exit_TEV,=$B$36*$B$37" + ","*years
    ending_debt_row = "ending_debt,=$B$38-$B$39" + ","*years
    ending_equity_row = "ending_equity,=$B$42-$B$43" + ","*years
    MOIC_row = "MOIC,=$B$44/$B$18" + ","*years
    csv_rows.append(exit_TEV_row)
    csv_rows.append(ending_debt_row)
    csv_rows.append(ending_equity_row)
    csv_rows.append(MOIC_row)


    csv_string = "\n".join(csv_rows)
    return csv_string

def to_excel(csv_string, file_path):
    # Read the CSV string into a DataFrame
    csv_data = pd.read_csv(StringIO(csv_string), header = None)

    # Write the DataFrame to an Excel file
    csv_data.to_excel(file_path, index=False, header=False, engine='openpyxl')

def calculate_lbo(entry_ass, is_ass):
    depreciation_ratio = is_ass['depreciation'] < 1
    rev_ratio = is_ass['rev_growth'] < 1
    capex_ratio = is_ass['capex_per_of_rev'] < 1
    
    if entry_ass["Rev_Y1"] / 1000000 < 1:
        entry_ass["Rev_Y1"] /= 1000000

    if is_ass["change_in_NWC"] / 1000000 < 1:
        is_ass["change_in_NWC"] /= 1000000

    if is_ass["depreciation"] / 1000000 < 1:
        is_ass["depreciation"] /= 1000000


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
        lbo_is[i].loc['Rev']=lbo_is[(i-1)].loc['Rev']*(1+is_ass['rev_growth']) if rev_ratio else lbo_is[(i-1)].loc['Rev'] + is_ass['rev_growth']
        i+=1
    
    lbo_is.loc['EBITDA']=lbo_is.loc['Rev']*entry_ass['EBITDA_Y1_Margin']

    lbo_is.loc['less: D&A']= -is_ass['depreciation'] if not depreciation_ratio else -is_ass['depreciation'] * lbo_is.loc['Rev']

    lbo_is.loc['EBIT']=lbo_is.loc['EBITDA']+lbo_is.loc['less: D&A']

    lbo_is.loc['less: Interest']=-is_ass['int_rate']*entry_ass['debt_portion']

    lbo_is.loc['EBT']=lbo_is.loc['EBIT']+lbo_is.loc['less: Interest']

    lbo_is.loc['less: Taxes']=lbo_is.loc['EBT']*-is_ass['tax_rate']

    lbo_is.loc['Earnings']=lbo_is.loc['EBT']+lbo_is.loc['less: Taxes']

    lbo_fcf=pd.DataFrame(data=None, index=["Earnings", "plus: D&A", "less: capex", "less: NWC", "FCF"], columns=years)

    lbo_fcf.loc['Earnings']=lbo_is.loc['Earnings']
    lbo_fcf.loc['plus: D&A']=-lbo_is.loc['less: D&A']
    lbo_fcf.loc['less: capex']=lbo_is.loc['Rev']*-is_ass["capex_per_of_rev"] if capex_ratio else lbo_is.loc['Rev']-is_ass["capex_per_of_rev"]
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
