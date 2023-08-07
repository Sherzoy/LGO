import pandas as pd

def read_text_to_excel(text, output_file):
    # Split the text into rows based on newline characters
    rows = text.strip().split('\n')

    # Extract the header and data from the rows
    header = rows[0].split('|')
    data = [row.split('|') for row in rows[2:]]

    # Clean up the header and data
    header = [col.strip() for col in header[1:-1]]
    data = [[col.strip() for col in row[1:-1]] for row in data]

    # Create a DataFrame from the data
    df = pd.DataFrame(data, columns=header)

    # Convert numeric columns (Age, Salary, Bonus) to integers or floats
    numeric_columns = ['Age', 'Salary', 'Bonus']
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

    # Calculate the 'Total Income' column
    df['Total Income'] = df['Salary'] + df['Bonus']

    # Save the DataFrame to an Excel file
    df.to_excel(output_file, index=False)

# Sample text response
sample_text = """
| Name       | Age | Occupation    | Salary   | Bonus   | Total Income  |
|------------|-----|---------------|----------|---------|---------------|
| John       | 30  | Engineer      | 70000    | 5000    | =C2+D2        |
| Emily      | 28  | Teacher       | 50000    | 3000    | =C3+D3        |
| Michael    | 35  | Doctor        | 90000    | 8000    | =C4+D4        |
| Sarah      | 32  | Lawyer        | 80000    | 6000    | =C5+D5        |
| Robert     | 29  | Software Eng  | 75000    | 5500    | =C6+D6        |
"""

# Output file name
output_file_name = 'sample_output.xlsx'

# Call the method to read the text into Excel
read_text_to_excel(sample_text, output_file_name)