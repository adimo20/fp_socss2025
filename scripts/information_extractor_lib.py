import pandas as pd
import google.generativeai as genai
from time import sleep
import os
from scripts.config_file import configs, generation_config
import json



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
        self.input_texts = self.df[self.text_colname]
        self.page_ids = self.df[self.page_id_colname]

    def loading_flow(self):
        flow = [self.set_config, self.load_model, self.load_data]
        for f in flow:
            f()
            print(f"{f} is done!")

    def create_model_input(self,page_id, input_text):
        self.model_input = {page_id:input_text}
        input_combined = f"{self.prompt}\n{self.model_input}"
        return input_combined
          

    def extract_single_page(self, page_id, input_text):
        input_combined = self.create_model_input(page_id=page_id, input_text=input_text)
        response = self.model.generate_content([input_combined])
        res_parsed = json.loads(response.text)
        print(res_parsed)
        return res_parsed
    
    def create_out_df(self, r:list):
        if os.path.isfile(self.output_filename):
            existing_df = pd.read_csv(self.output_filename, sep=";")
            new_df = pd.DataFrame(data={"page_id":[c["page_id"] for c in r], "text":[c["content"] for c in r]})
            combined_df = pd.concat([existing_df, new_df])
            
            return combined_df
        
        else: 
            new_df = pd.DataFrame(data={"page_id":[c["page_id"] for c in r], "text":[c["content"] for c in r]})
            return new_df
    
    def check_model_output(self, model_output, i):
        if "page_id" in model_output and "content" in model_output:
            return model_output
        elif "page_id" not in model_output:
            model_output.update({"page_id":self.page_ids[i]})
            return model_output
        else: 
            model_output.update({"content":"Nothing found in here"})
            return model_output
            


    def extract_data_loop(self, max_n):
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
        


###########################################
###########################################


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
        num_cases = len(self.df)
        lower_boundary = [i for i in range(0,num_cases) if i % batch_size == 0]
        upper_boundary = [i for i in range(0,num_cases) if i % batch_size == 0][1:]
        upper_boundary[len(upper_boundary)-1] = num_cases-1
        self.upper_boundary = upper_boundary
        lower_boundary = lower_boundary[:len(lower_boundary)-1]
        self.lower_boundary = lower_boundary
        
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




    
