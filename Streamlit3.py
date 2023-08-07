# -*- coding: utf-8 -*-
"""
Created on Thu Jul 27 17:26:18 2023

@author: aivam
"""

import pandas as pd
import streamlit as st 

import pulp   

def predict_Y(df):
    
    
    df.rename(columns = {'Customer Name':"Party Name","Plant":"Warehouse","Target Quantity":"Net Weight"},inplace = True)
    warehouses = df['Warehouse'].unique()
    party_names = df['Party Name'].unique()
    df['Freight_Rate'] = 0
    for i in df.index:
        if (df['Warehouse'][i] == 'GIR'):
            df.at[i, 'Freight_Rate'] = 2.9
        elif (df['Warehouse'][i] == 'GIR II'):
            df.at[i, 'Freight_Rate'] = 2.9
        elif (df['Warehouse'][i] == 'KSR4'):
            df.at[i, 'Freight_Rate'] = 2.5
        elif (df['Warehouse'][i] == 'LKDRM2') and df['Distance'][i] <= 40:
            df.at[i, 'Freight_Rate'] = 100
        elif (df['Warehouse'][i] == 'LKDRM2') and df['Distance'][i] > 40:
            df.at[i, 'Freight_Rate'] = 2.5
        elif (df['Warehouse'][i] == 'RSDSH') and df['Distance'][i] <= 40:
            df.at[i, 'Freight_Rate'] = 100
        elif (df['Warehouse'][i] == 'RSDSH') and df['Distance'][i] > 40:
            df.at[i, 'Freight_Rate'] = 2.5
        elif (df['Warehouse'][i] == 'SLKPY') and df['Distance'][i] <= 40:
            df.at[i, 'Freight_Rate'] = 100
        elif (df['Warehouse'][i] == 'SLKPY') and df['Distance'][i] > 40:
            df.at[i, 'Freight_Rate'] = 2.5
    
    df['shipping_cost'] = 0
    for i in df.index:
        if (df['Freight_Rate'][i] == 100):
            df.at[i, "shipping_cost"] = df.at[i, 'Freight_Rate']
        elif (df['Freight_Rate'][i] < 100):
            df.at[i, "shipping_cost"] = df.at[i, 'Freight_Rate'] * df.at[i, 'Distance']
    distance_matrix = df.pivot_table(values= 'Distance', index='Warehouse', columns='Party Name')
    # fill with 10000 Wherever no supply
    distance_matrix.fillna(10000, inplace = True)
    

    # Create a pivot table with Warehouse as index, Party Name as columns, and freight rate as values
    freight_mat = df.pivot_table(values = 'Freight_Rate', index = 'Warehouse', columns = 'Party Name')
    # Fill with 10000 wherever no supply
    freight_mat.fillna(100000, inplace = True)
    

    # Create a pivot table with Warehouse as index, Party Name as columns, and shipping cost as values
    cost_mat = df.pivot_table(values = 'shipping_cost', index = 'Warehouse', columns = 'Party Name')
    #fill with 100000 wherever no supply
    cost_mat = cost_mat.fillna(100000)
    

    # Create a pivot table with Warehouse as index, Party Name as columns, and Net weight as values
    weight_mat = df.pivot_table(values = 'Net Weight', index = 'Warehouse', columns = 'Party Name', aggfunc =sum )
    # fill with zeros wherever no sulpply
    weight_mat = weight_mat.fillna(0)
    

    # Manually Assign Maximum Supply Values For All Warehouse
    supply = {'GIR': 1000000,'GIR II': 1000000,'KSR4': 1000000,'LKDRM2': 1000000,'RSDSH': 1000000,'SLKPY': 1000000}
    

    #create a pivot_tabel for total demand of each party (Before optimization the Quantity of sand Transport from Warehouse the Party)
    demand = pd.pivot_table(df, values='Net Weight', columns ='Party Name', aggfunc = sum)
    

    # Define the problem
    prob = LpProblem("Transportation Problem", LpMinimize)

    # Define decision variables
    route_vars = LpVariable.dicts("Route", (warehouses, party_names), lowBound=0, cat='Continuous')
    

    # Define the objective function
    prob += lpSum([route_vars[w][p] * cost_mat.loc[w][p] for w in warehouses for p in party_names]), " Transportation Cost"
    for w in warehouses:
        prob += lpSum([route_vars[w][p]   for p in party_names]) <= supply[w] , "Sum of quatity supplied from Warehouse to paty %s" % w
    demand2 = demand.T
    
    for p in party_names:
        prob += lpSum([route_vars[w][p] for w in warehouses]) >= demand2.loc[p], 'Sum of Demand of party %s' % p
    prob.solve()
    print('Total_transportation_Costs = {:,} '.format(int(value(prob.objective))))

    # shows the status of the Problem
    print(f"Status: {LpStatus[prob.status]}")

    # Create DataFrame
    decision_var_df = pd.DataFrame(index=distance_matrix.index, columns=distance_matrix.columns, dtype='float')

    # Fill the DataFrame with the optimized values of the decision variables
    for w in distance_matrix.index:
        for p in distance_matrix.columns:
            decision_var_df.loc[w, p] = route_vars[w][p].varValue

    # Decision_Variables(How Much Quantity of Sand Transport form Warehouse to Party )
    decision_var_df
    total_after_opt = [decision_var_df.loc[w][p] * cost_mat.loc[w][p] .sum().sum() for w in warehouses for p in party_names]

    total1 = sum(total_after_opt)
    print('total_cost_after_opt',total1)
    total1

    # Before_Optimization the Transportation Cost in ₹
    before_opt_cost = df['Amount'].sum()
    before_opt_cost

    #Total Cost - Total Minimized Cost
    print("Difference_ before- after:",(before_opt_cost) -  sum(total_after_opt))

    # Calculating the percentage decrease in total transportation cost
    print("percentage_decrease:",((((before_opt_cost) -  sum(total_after_opt)))/((before_opt_cost)))*100)

 
   

    # save the weight_matrix in csv format
    weight_mat.to_csv('inital_weight_june23_actual.csv')
    return decision_var_df 
       
   
  
    
    
    
    
    



def main():

    st.title("Optimization projects")
    st.sidebar.title("July month data")

    html_temp = """
    <div style="background-color:tomato;padding:10px">
    <h2 style="color:white;text-align:center;">July report </h2>
    </div>
    
    """
    st.markdown(html_temp, unsafe_allow_html = True)
    st.text("")
    

    uploadedFile = st.sidebar.file_uploader("Upload a file" , type = ['csv','xlsx'], accept_multiple_files = False, key = "fileUploader")
    if uploadedFile is not None :
        try:

            df = pd.read_excel(uploadedFile)
        except:
                try:
                    df = pd.read_(uploadedFile)
                except:      
                    df = pd.DataFrame(uploadedFile)
        
        
    else:
        st.sidebar.warning("Upload a CSV or Excel file.")
    
 
    
    if st.button("Predict"):
        result = predict_Y(df)
                           
      
        

                           
if __name__=='__main__':
    main()

