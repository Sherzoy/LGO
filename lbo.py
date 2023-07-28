import pandas as pd
import numpy as np



def calculate_lbo(entry_ass, is_ass):
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

    print(exit_returns)

entry_ass = {
    "entry_multiple": 5.0,
    "Rev_Y1": 100,
    "EBITDA_Y1_Margin": 0.40,
    "debt_ratio": 0.60,
    "equity_ratio": 0.40,
    "years": 5
}

is_ass = {
    "rev_growth": 0.10,
    "int_rate": 0.10,
    "tax_rate": 0.40,
    "capex_per_of_rev": 0.15,
    "change_in_NWC": 5,
    "depreciation": 20
  }

calculate_lbo(entry_ass, is_ass)