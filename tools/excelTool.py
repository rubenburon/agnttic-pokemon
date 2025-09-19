import os
import glob
import requests
import re
import pandas as pd
from smolagents import tool

# este archivo contiene una tool para un smol agent, 
# hay que usar el decorador @tool
# además, hay que documentar la función con una descripción, 
# los argumentos y lo que devuelve, 
# porque el agente se lee esa descripción para invocar a la función.



@tool
def read_excel_file(filename: str) -> pd.DataFrame:
    """Reads an Excel file from disk into a pandas DataFrame.
    
    Args:
        filename: The path of the file to be read.
    Returns:
        A pandas DataFrame containing the content of the Excel file or None if the download failed.
    """
    try:
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(filename, engine='openpyxl')
        return df
    except Exception as e:
        print(f"Error reading Excel file {filename}: {e}")
        return None



@tool
def write_excel(dataframe:pd.DataFrame, filename:str)->None:
    """Writes the content of a pandas dataframe into an Excel file.

    Args:
        dataframe: A pandas dataframe.
        filename: a string with the name of the file to be written.
    Returns: 
        None
    """
    try:
        dataframe.to_excel(filename)
    except Exception as e:
        print(f"Error writting excel file {filename}: {e}")
        return None
