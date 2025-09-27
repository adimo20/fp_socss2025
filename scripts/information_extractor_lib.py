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
from rapidfuzz import fuzz
import re 
import nltk

def is_sentence(sent, threshold):
    if sent == []:
        return False
    
    return len(nltk.word_tokenize(sent)) > threshold


def preprocess_raw_text(text:str)->str:
    """Every character that in not a alpha-numeric letter or element of the list ['.', '-', ','] will be removed. Also all duplicated spaces will be replaced by just one space.
    Parameters: 
    Raw Text

    Returns:
    cleaned text
    """
    pattern = [r"[^\w|\s|\.|-|\,]", r"\s+"]
    for p in pattern:
        text = re.sub(p, " ", text)
    text = text.strip()
    return text 


if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def get_time_str() -> str:
    t = str(datetime.now())
    t = t[0:16].replace(":", "_").replace(" ", "_")
    return t

def create_output_path_with_time_stamp(output_path:str)-> str:
    return output_path.replace(".csv", get_time_str()) + ".csv"

class DataManager:
    def __init__(self, input_df, output_df):
        self.input_df = input_df
        self.output_df = output_df

    def reduce_input_df(self) -> None:
        time = get_time_str()
        if not os.path.isdir("archive"): os.makedirs("archive")
        #filename nicht hardcoden oder einen generischen Namen verwenden
        self.input_df.to_csv("archive/newspaper_concat"+ time + ".csv", sep = ";", index = False)
            
        #Rausfilter der bereits verarbeiteten page_ids und abspeichern für das nächste mal  
        self.input_df = self.input_df[self.input_df.page_id.apply(lambda s: s not in self.output_df.page_id.to_list())]
        self.input_df.to_csv("newspaper_concat.csv", sep=";", index= False)
        return


class InformationExtractor:
    def __init__(self, df:pd.DataFrame,page_id_colname:str, text_colname:str, output_filename:str=None):
        self.configs = configs
        #Das hier könnte zu problemen führen
        self.model_name:str = None
        self.prompt:str = None
        self.model:str = None
        self.page_ids:list = None
        self.input_texts:list = None
        self.df:pd.DataFrame = df
        self.model_input = None
        self.page_id_colname:str = page_id_colname
        self.text_colname:str = text_colname
        self.output_filename:str = output_filename
        self.sleeping_time:int = 4 #This is critical - because if the model responds to fast too often then this will result in ratelimit errors. 
        #By default no results are saved
        self.safe_results_external:bool = False
        self.generation_config = generation_config
        self.verbose:bool = False #if true prints out the extracted contet
        self.save_one_result_per_row:bool = True
        
        
    def set_config(self) -> None:
        """Setzen des API Keys, aus den im config dict gespeicherten Daten"""
        API_KEY = self.configs["API_KEY"]
        if self.model_name is None:
            self.model_name:str = self.configs["model_name"]
        if self.prompt is None:
            self.prompt:str = self.configs["PROMPT"]
        genai.configure(api_key=API_KEY)

    def load_model(self) -> None:
        """Laden des Models und setzen der Modelkonfigurationen. Generation Config sollte im config_file gespeichert sein"""
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config)
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
            if self.verbose: print(f"{f} is done!")

    def create_model_input(self,page_id:str, input_text:str) -> str:
        """Funktion die den prompt erstellt, der später an die Model API gesendet wird
        Parameters:
        page_id - id des inputs
        input_text - Text der als Input für das Model verwendet wird

        Returns:
        string that combines the input text and input prompt
        
        """
        self.model_input = {page_id:input_text}
        input_combined = f"{self.prompt}\n{self.model_input}"
        return input_combined
          

    def extract_single_page(self, page_id:str, input_text:str) -> dict:
        """Funktion die die API anspricht und die einen strukturierten Output als response erhält
        Parameters:
        page_id - id des inputs
        input_text - Text der als Input für das Model verwendet wird

        Returns:
        model response
        """
        try:
            input_combined = self.create_model_input(page_id=page_id, input_text=input_text)
            
        except Exception as e:
            print(f"Error while generating the model input: {e}")
            return {"content":f"Error while generating the model input: {e}"}
        
        try:
            response = self.model.generate_content([input_combined])
        except Exception as e:
            print(f"Error while receiving the response: {e} ")
            return {"content":f"Error while receiving the response: {e} "}
        
        try:
            res_parsed = json.loads(str(response.text))

            return res_parsed
        except Exception as e: 
            print(f"Error while parsing the response - Exeption {e}")
            return {"content":f"Error while parsing the response - Exeption {e}"}
                
        
    def create_out_df(self, r:list[dict]) -> pd.DataFrame:
        """Funktion die aus dem Model output einen Dataframe produziert"""
        page_id_list = [c["page_id"] if c is not None and "page_id" in c and c["page_id"] is not None else None for c in r]
        text_list = [c["content"] if c is not None and "content" in c and c["content"] is not None else None for c in r]
        time_str = get_time_str()
        
        new_df = pd.DataFrame(data={"page_id":page_id_list, "text":text_list, "time":time_str})
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
            
    def reduce_future_input(self, input_df, output_df) -> None:
        dm_reduce_processed_data = DataManager(input_df=input_df, output_df=output_df)
        dm_reduce_processed_data.reduce_input_df()
        return
        

    def extract_data_loop(self, max_n:int)-> pd.DataFrame:
        """Loop der die Informationsextraction durchführt. 0:n-te Zeilen des Input df werden verarbeitet."""
        self.loading_flow()
        res_list = []
        for i in range(0, max_n):
            res_temp = self.extract_single_page(self.page_ids[i], self.input_texts[i])
            res_temp = self.check_model_output(model_output=res_temp, i=i)
            res_list.append(res_temp)
            if self.verbose: print(res_temp)
            sleep(self.sleeping_time)
            if i % 100 == 0 and self.safe_results_external:
                res_list_df_temp = self.create_out_df(res_list)
                self.reduce_future_input(input_df=self.df, output_df=res_list_df_temp)
                res_list_df_temp.to_csv(self.output_filename, sep=";", index=False)
        
        res_list_df = self.create_out_df(res_list)
        #Important content of text needs to be a list otherwise this wont work - this is wrong literally safes one resut per row or am i wrong
        if self.save_one_result_per_row and not res_list_df.empty and isinstance(res_list_df.text[0], list): 
            #filter text == [] split an dieser stelle und danach concat.
            res_list_df = pd.concat([
                res_list_df[res_list_df.text.apply(lambda s: s == [])].reset_index(drop=True),
                res_list_df[res_list_df.text.apply(lambda s: s != [])].explode('text').reset_index(drop=True)
            ])
            
        #Final output will then be timestamped
        if self.safe_results_external:
            self.reduce_future_input(input_df=self.df, output_df=res_list_df)
            out_filename_timestamped = create_output_path_with_time_stamp(self.output_filename)
            res_list_df.to_csv(out_filename_timestamped, sep=";", index=False)   
        return(res_list_df)
        

class ExtractionValidator:
    def __init__(self,dst_doc:list=None, source_doc:list=None, threshold:float=None):
        self.dst_doc = dst_doc
        self.source_doc = source_doc
        self.threshold = threshold

    def find_similiar_sequence(self, dst_doc:str, source_doc:str, threshold:float, break_when_threshold:bool) -> pd.DataFrame:
        """Checks if the extracted content is with a certain threshold in the given document. If a 1:1 match is found it directly returns 
        True - if not levenstein distance is used to check if the extracted string is in the document with a certain threshold of stringsimiliarties
        Parameters:
            dst_doc: str - extracted content
            source_doc: str -  original document
            threshold: float - threshold for stringsimiliarities 
            return_msk: bool - parameter True - just return the mask if val is in doc or false the df with the matches and the ratio will be returned
        Returns:
            pd.DataFrame containing the potential matches
        """
        
        n = len(dst_doc)
        n_src = len(source_doc)
        i = 0

        best_match_list = []
        best_ratio_list = []
        while n < n_src:
            stringsim = fuzz.ratio(dst_doc, source_doc[i:n])/100
            if stringsim > threshold: 
                best_match_list.append(source_doc[i:n])
                best_ratio_list.append(stringsim)
                if break_when_threshold:
                    break
            i += 1
            n += 1

        matches_df = pd.DataFrame(data={"ratio":best_ratio_list, "match":best_match_list, "extracted":dst_doc})
        
        return matches_df
    
    def is_match(self, dst_doc:str, source_doc:str, threshold:float) -> bool:
        """Checks if a match was found. Check if the text is either one to one in the match or it is within the threshold similiar
        Parameters:
            dst_doc: str - extracted content
            source_doc: str -  original document
            threshold: float - threshold for stringsimiliarities 
            return_msk: bool - parameter True - just return the mask if val is in doc or false the df with the matches and the ratio will be returned
        Returns:
            True if String is in the original document False if it is not in the document within the threshold   
        
        
        """
        
        if dst_doc in source_doc: return True
        match_df = self.find_similiar_sequence(dst_doc, source_doc, threshold, break_when_threshold=True)
        if len(match_df) > 0:
            return True
        else:
            return False
        
    def apply_is_match_on_data(self) -> list[bool]:
        """Applys is_match over all data - Can be used as a mask to filter the values that are not correctly extracted
        
        Parameter:
        None

        Return: 
        List of bool values that determining if the given extracted text was is in (True) the source text within the given threshold or not (False)

        """
        found_match_list:list[bool] = [self.is_match(d, s, self.threshold) for d, s in zip(self.dst_doc, self.source_doc)]
        return found_match_list
    
    def calculate_extraction_accuracy(self) -> tuple:
        """Return tuple with the accuracy of the text extraction"""
        n = len(self.dst_doc)
        match_bool = self.apply_is_match_on_data()
        true_positive = sum(match_bool)
        
        return ("Accuracy", true_positive/n)

    
      


if __name__ == "__main__":
    dat_joined = pd.read_pickle("dat_joined.pkl")
    validation = ExtractionValidator(dst_doc=dat_joined.text.tolist(), source_doc=dat_joined.plainpagefulltext.tolist(), threshold=0.98)
    result = validation.calculate_extraction_accuracy()
    print(result)
    #In case you want to just check one text        
    validator = ExtractionValidator(dst_doc=None, source_doc=None, threshold=None)
    result2 = validator.find_similiar_sequence(dst_doc=dat_joined.text[0], source_doc=dat_joined.plainpagefulltext[0], threshold=0.98, break_when_threshold=False)
    result2

    