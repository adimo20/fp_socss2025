import pandas as pd
import google.generativeai as genai
from time import sleep
import os
from scripts.config_file import configs, generation_config
import json
import sys
import io
from datetime import datetime
import sys
import io

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def get_time_str() -> str:
    t = str(datetime.now())
    t = t[0:16].replace(":", "_").replace(" ", "_")
    return t


class DataManager:
    def __init__(self, input_df, output_df):
        self.input_df = input_df
        self.output_df = output_df

    def reduce_input_df(self) -> None:
        time = get_time_str()
        self.input_df.to_csv("archive/newspaper_concat"+ time + ".csv", sep = ";", index = False)
            
        #Rausfilter der bereits verarbeiteten page_ids und abspeichern für das nächste mal  
        self.input_df = self.input_df[self.input_df.page_id.apply(lambda s: s not in self.output_df.page_id)]
        self.input_df.to_csv("newspaper_concat.csv", sep=";", index= False)
        return


class InformationExtractor:
    def __init__(self, df:pd.DataFrame,page_id_colname:str, text_colname:str, output_filename:str):
        self.model_name:str = configs["model_name"]
        self.prompt:str = configs["PROMPT"]
        self.model:str = None
        self.page_ids:list = None
        self.input_texts:list = None
        self.df = df
        self.model_input = None
        self.page_id_colname = page_id_colname
        self.text_colname = text_colname
        self.output_filename = output_filename
        
    def set_config(self) -> None:
        """Setzen des API Keys, aus dem config_file"""
        API_KEY = configs["API_KEY"]
        genai.configure(api_key=API_KEY)

    def load_model(self) -> None:
        """Laden des Models und setzen der Modelkonfigurationen"""
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config)
        self.initialized_model = True
        
    def load_data(self) -> None:
        """Einlesen der Daten aus dem Input-Path und speichern in den Variablen input_texts, page_id"""
        self.input_texts = self.df[self.text_colname]
        self.page_ids = self.df[self.page_id_colname]

    def loading_flow(self) -> None:
        """Flow der das Model im Objekt InformationExtractor lädt und es im init speichert."""
        flow = [self.set_config, self.load_model, self.load_data]
        for f in flow:
            f()
            print(f"{f} is done!")

    def create_model_input(self,page_id:str, input_text:str) -> str:
        """Funktion die den prompt erstellt, der später an die Model API gesendet wird"""
        self.model_input = {page_id:input_text}
        input_combined = f"{self.prompt}\n{self.model_input}"
        return input_combined
          

    def extract_single_page(self, page_id:str, input_text:str) -> dict:
        """Funktion die die API anspricht und die einen strukturierten Output als response erhält"""
        input_combined = self.create_model_input(page_id=page_id, input_text=input_text)
        response = self.model.generate_content([input_combined])
        res_parsed = json.loads(response.text)
        print(res_parsed)
        return res_parsed
    
    def create_out_df(self, r:list[dict]) -> pd.DataFrame:
        """Funktion die aus dem Model output einen Dataframe produziert. """
        new_df = pd.DataFrame(data={"page_id":[c["page_id"] for c in r], "text":[c["content"] for c in r]})
        return new_df
    
    def check_model_output(self, model_output:dict, i:int) -> dict:
        """Funktion die den Model Output validiert. Falls es einen Fehler gab bei der API-Response - wird das jeweilige Element 
        imputiert. Falls es keine Page id gibt wird die aktuelle ID nachgetragen, wenn kein Text aber eine page_id da ist, geben wir 
        der Response einen Content der sag, das wir keine Informationen extrahieren konnten"""
        if "page_id" in model_output and "content" in model_output:
            return model_output
        elif "page_id" not in model_output:
            model_output.update({"page_id":self.page_ids[i]})
            return model_output
        else: 
            model_output.update({"content":"Nothing found in here"})
            return model_output
            

    def extract_data_loop(self, max_n:int)-> pd.DataFrame:
        """Loop der die Informationsextraction durchführt. 0:n-te Zeilen des Input df werden verarbeitet."""
        self.loading_flow()
        res_list = []
        for i in range(0, max_n):
            res_temp = self.extract_single_page(self.page_ids[i], self.input_texts[i])
            res_temp = self.check_model_output(model_output=res_temp, i=i)
            res_list.append(res_temp)
            sleep(6)
            if i % 5 == 0:
                res_list_df_temp = self.create_out_df(res_list)
                res_list_df_temp.to_csv(self.output_filename, sep=";", index=False)
        
            
        res_list_df = self.create_out_df(res_list)
        return(res_list_df)
        


