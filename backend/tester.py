import json
import pandas as pd
from io import StringIO

def makeExcel(jsondata):
    data = json.loads(jsondata)

    entry_ass = data["entry_ass"]
    is_ass = data["is_ass"]
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

def csv_to_excel(csv_string, file_path):
    # Read the CSV string into a DataFrame
    csv_data = pd.read_csv(StringIO(csv_string), header = None)

    # Write the DataFrame to an Excel file
    csv_data.to_excel(file_path, index=False, header=False)


data = {
    "entry_ass": {
        "entry_multiple": 5,
        "Rev_Y1": 100000000,
        "EBITDA_Y1_Margin": 0.4,
        "debt_ratio": 0.6,
        "equity_ratio": 0.4,
        "years": 4
    },
    "is_ass": {
        "rev_growth": 0.1,
        "int_rate": 0.1,
        "tax_rate": 0.4,
        "capex_per_of_rev": 0.15,
        "change_in_NWC": 5000000,
        "depreciation": 20000000
    }
}

json_string = json.dumps(data, indent=4)
csv_string= makeExcel(json_string)
print(csv_string)
csv_to_excel(csv_string, "output.xlsx")