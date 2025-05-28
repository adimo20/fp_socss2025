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
        
    def set_config(self):
        """Setzen des API Keys, aus dem config_file"""
        API_KEY = configs["API_KEY"]
        genai.configure(api_key=API_KEY)

    def load_model(self):
        """Laden des Models und setzen der Modelkonfigurationen"""
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config)
        self.initialized_model = True
        
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
    
    def information_extraction_flow(self):
        """Workflow für die Informationsextraction!"""
        flow = [self.set_config, self.load_model, self.load_data, self.check_output_path, self.extract_informations]

        for f in flow:
            f()
            print(f"{f} is done!", flush=True)
    
#######################################################################

class OcrCorrecter:
    def __init__(self, model_name:str, df, page_id_colname:str, text_colname:str):
        self.model_name:str = model_name
        self.prompt:str = configs["PROMPT"]
        self.model:str = None
        self.df: pd.DataFrame = df
        self.string_for_ocr_correction:str = None
        self.prompt_for_ocr_correction:str = configs["prompt_ocr_correction"]
        self.initialized_model:bool = False
        self.lower_boundary:int = None
        self.upper_boundary:int = None
        self.page_id_colname:str =page_id_colname
        self.text_colname:str = text_colname
    
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

    def create_batch_boundries(self) -> None:
        batch_size = configs["batch_size"]
        lower_boundary = [i for i in range(0,len(self.df)) if i % batch_size == 0]
        self.upper_boundary = [i for i in range(0,len(self.df)) if i % batch_size == 0][1:]
        self.lower_boundary = lower_boundary[:len(lower_boundary)-1]

    def create_json_str(self, df, lower, upper) -> str:
        """Creates a json format string containing the keys - page_id and values text - the ocr-error
        texts. It is as big as the batch size"""    
        j_list = [{ p : t} for p, t in zip(df[self.page_id_colname], df[self.text_colname])]
        test_list = j_list[lower:upper]
        test_list_str = json.dumps(test_list)
        return test_list_str
        
    def correct_ocr(self) -> str:
        """Sends a string in json format contaning the ocr-error texts and the given page_ids
        as keys to the api and receives a corrected version of the json string."""
        response = self.model.generate_content([self.prompt_for_ocr_correction, self.string_for_ocr_correction])
        patterns_to_remove = ["```json", "```", "\n"]
        response_text = response.text
        for p in patterns_to_remove:
            response_text = response_text.replace(p, "")

        self.ocr_corrected_json = response_text
    
    def json_to_df(self) -> pd.DataFrame:

        """Turns the json-output from api response to a dataframe - at first it 
        seperates the the keys from the values and the saves both i seprate columns.
        Meaning a df that contains the columns page_id and text."""
        
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
    
    def ocr_correction_flow(self) -> pd.DataFrame:
        """Workflow für die Ocr-Correction!"""
        flow = [self.set_config, self.load_model, self.correct_ocr, self.json_to_df]

        for i, f in enumerate(flow):
            
            if self.initialized_model and i < 2: continue 
            print(f"{f} is done!", flush=True)
            
            if i < 3:
                f()
            else:
                result = f()
                print(f"{f} is done!", flush=True)
                return result
    
    def run_batched_correction_flow(self) -> None:
        self.create_batch_boundries()
        res_list = []   
        for l, u in zip(self.lower_boundary, self.upper_boundary):
            j_string = self.create_json_str(self.df, l, u)
            self.string_for_ocr_correction = j_string
            resp = self.ocr_correction_flow()
            res_list.append(resp)
            if u % 200 == 0:
                res_df = pd.concat(res_list)
                res_df.to_csv("corrected_df.csv", sep=";")


if __name__ == "__main__":
    extractor = information_extractor(input_path="newspaper_concat.csv", output_path="page_id_plus_texts.csv", model_name="gemini-1.5-flash")
    extractor.information_extraction_flow()

    df = pd.read_csv("page_id_plus_texts.csv", converters={"page_id_plus_texts":ast.literal_eval}, sep = ";")
    df["page_id"], df["text"] = df.page_id_plus_texts.apply(lambda l: str(l[0])), df.page_id_plus_texts.apply(lambda l: l[1])
    ocr_cor = OcrCorrecter(model_name="gemini-1.5-flash", df=df, page_id_colname="page_id", text_colname="text")
    ocr_cor.run_batched_correction_flow()

    



