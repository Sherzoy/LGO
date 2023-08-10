import pandas as pd
import io

def convert_csv_to_excel(csv_text, excel_file_path):
    # Read the CSV data using pandas
    data = pd.read_csv(io.StringIO(csv_text), index_col=0)
    
    # Create an Excel writer
    excel_writer = pd.ExcelWriter(excel_file_path)
    
    # Write the data to the Excel file
    data.to_excel(excel_writer, sheet_name='Sheet1')
    
    # Save the Excel file
    excel_writer.save()

# Sample CSV text
sample_csv_text = """Name,Age,Occupation,Salary,Bonus,Total Income
John,30,Engineer,70000,5000,=D2+E2
Emily,28,Teacher,50000,3000,=D3+E3
Michael,35,Doctor,90000,8000,=D4+E4
Sarah,32,Lawyer,80000,6000,=D5+E5
Robert,29,Software Eng,75000,5500,=D6+E6"""

# Output file name
output_file_name = 'sample_output.xlsx'

# Call the method to convert the CSV text to Excel
convert_csv_to_excel(sample_csv_text, output_file_name)
