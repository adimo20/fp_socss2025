from scripts.information_extractor_lib import InformationExtractor
from scripts.config_file import configs, generation_config
import pandas as pd
from full_workflow_config import fw_config

dat_joined_complete = pd.read_pickle("dat_joined.pkl")

dat_joined = dat_joined_complete.head(100)

ocr_corrector = InformationExtractor(df=dat_joined, page_id_colname="page_id", text_colname="text", output_filename="ocr_corrected_df.csv")
#Set the configs for the task to perform
ocr_corrector.prompt = fw_config["CORRECTION_PROMPT"]
ocr_corrector.model_name = fw_config["model_name"]
data_corrected = ocr_corrector.extract_data_loop(100)


word_completion = InformationExtractor(df=data_corrected, page_id_colname="page_id", text_colname="text", output_filename="ocr_corrected_df.csv")

word_completion.prompt = fw_config["COMPLETION_PROMPT"]
word_completion.model_name = fw_config["model_name"]
data_word_completed = word_completion.extract_data_loop(100)


data_word_completed.columns = ['page_id_completed', 'text_completed', 'time_completed']
merged_df = pd.concat([data_corrected, data_word_completed], axis = 1)
merged_df = merged_df.filter(["text", "text_completed"])
print(merged_df)
merged_df.to_csv("merged_df_100.csv")
