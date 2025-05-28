import pandas as pd
import google.generativeai as genai
import sys
import io
from time import sleep
import ast
import os
from config_file import configs, generation_config
import json
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')



class information_extractor:
    def __init__(self, input_path: str, output_path:str, model_name:str):
        self.input_path:str = input_path
        self.output_path:str = output_path
        self.model_name:str = model_name
        self.prompt:str = configs["PROMPT"]
        self.model:str = None
        self.page_ids:list = None
        self.input_texts:list = None
        self.df = None
        self.string_for_ocr_correction = None
        self.prompt_for_ocr_correction = configs["prompt_ocr_correction"]

    def set_config(self):
        """Setzen des API Keys, aus dem config_file"""
        API_KEY = configs["API_KEY"]
        genai.configure(api_key=API_KEY)

    def load_model(self):
        """Laden des Models und setzen der Modelkonfigurationen"""
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config)
        
    def load_data(self):
        """Einlesen der Daten aus dem Input-Path und speichern in den Variablen input_texts, page_id"""
        self.df = pd.read_csv(self.input_path, sep=";")
        self.input_texts = self.df["plainpagefulltext"]
        self.page_ids = self.df["page_id"]

    def check_output_path(self):
        if not os.path.isfile(self.output_path):
            results_df = pd.DataFrame(data={"page_id_plus_texts":[""]})
            results_df.to_csv(self.output_path)
        return
            

    def append_existing_df(self, results):
        """Speichern der neu extrahierten Informationen in den dataframe hinterlegt in output_path."""
        
        if len(results) > 0:
            exististing_df = pd.read_csv(self.output_path, sep=";")  
            results_df = pd.DataFrame(data={"page_id_plus_texts":results})
            results_df = pd.concat([exististing_df, results_df])
            results_df = results_df[results_df.duplicated() == False]
            results_df.to_csv(self.output_path, sep=";", index=False)
        else: 
            return

    def reduce_input_for_next_run(self, page_ids):
        """Entfernen der bereits verarbeiteten Seiten aus dem Input dataframe und abspeichern des reduzierten Dataframe"""
        self.df = self.df[self.df.page_id.apply(lambda s: s not in page_ids)]
        self.df.to_csv(self.input_path, sep=";")

    def extract_informations(self):
        """Funktion die die Informationen im gegebenen Text durch die gemini API kondensiert."""

        results = []
        processed_ids = []
        for page_id, input_text, i in zip(self.page_ids, self.input_texts, range(len(self.input_texts))):
            
            print(f"Reached {i}-th text.", flush=True)
            processed_ids.append(page_id)
            response = self.model.generate_content([self.prompt, input_text])
            print(response, flush=True)
            patterns_to_remove = ["```python", "```", "\n"]
            response = response.text
            for p in patterns_to_remove:
                response = response.replace(p, "")
            
            try:
                response = ast.literal_eval(response)
            except Exception as e:
                print("Failed to parse:", e)
            
            try:
                if response is not None or response != []:
                    if len(response) > 1 and isinstance(response, list):
                        for r in response:
                            results.append((page_id, r))
                    elif len(response) == 1 and isinstance(response, list):
                        results.append((page_id,response[0]))

                    

            except:
                print("Error while appending the output-list!")
            print(f"extract this: {response}", flush=True)
            sleep(6)
            del(response)

            if i % 20 == 0:
                #Hier könnte man noch einen Feedback loop einbauen!
                print("Saved the results!!!", flush=True)
                self.append_existing_df(results=results)
                self.reduce_input_for_next_run(page_ids=processed_ids)
            
            if i == 500:
                break
    
    def correct_ocr(self):
        response = self.model.generate_content([self.prompt_for_ocr_correction, self.string_for_ocr_correction])
        patterns_to_remove = ["```json", "```", "\n"]
        response_text = response.text
        for p in patterns_to_remove:
            response_text = response_text.replace(p, "")

        self.ocr_corrected_json = response_text
    
    def json_to_df(self):
        
        def get_value_key(r):
            value = r.values()
            string = list(value)[0]
            key_dict = r.keys()
            key = list(key_dict)[0]
            return key, string

        resp = self.ocr_corrected_json
        page_ids, texts = [], []
        json_list = json.loads(resp)
        for r in json_list:
            key, string = get_value_key(r)
            page_ids.append(key)
            texts.append(string)

        corrected_df = pd.DataFrame(data={"page_id" : page_ids, "texts": texts})
        return corrected_df     

    def information_extraction_flow(self):
        """Workflow für die Informationsextraction!"""
        flow = [self.set_config, self.load_model, self.load_data, self.check_output_path, self.extract_informations]

        for f in flow:
            f()
            print(f"{f} is done!", flush=True)
    
    def ocr_correction_flow(self):
        """Workflow für die Ocr-Correction!"""
        flow = [self.set_config, self.load_model, self.correct_ocr, self.json_to_df]

        for i, f in enumerate(flow):
            print(f"{f} is done!", flush=True)
            if i != 3:
                f()
            else:
                result = f()
                print(f"{f} is done!", flush=True)
                return result
            



if __name__ == "__main__":
    extractor = information_extractor(input_path="newspaper_concat.csv", output_path="page_id_plus_texts.csv", model_name="gemini-1.5-flash")
    extractor.information_extraction_flow()
    







    
