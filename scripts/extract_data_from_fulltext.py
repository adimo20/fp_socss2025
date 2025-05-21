import pandas as pd
import google.generativeai as genai
import sys
import io
from time import sleep
import ast
from config_file import configs
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

df = pd.read_csv("newspaper_concat.csv", sep=";")

API_KEY = configs["API_KEY"]
genai.configure(api_key=API_KEY)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b",
    generation_config=generation_config,
)

chat = model.start_chat(history=[])

output_list = []
results = []
prompt = "Your porpouse is it to extract a pre-defined part of the text i will provide you. The text i'll provide you is an ocr read" \
"historical newspaper. Your task is it to extract the marriage request from the text. It is possible that there are more than one in the text" \
"in this case extract all of them. If you are done, reevaluate your work and check your results. Return the results in the format of a python list." \
"The response should be just the text you extracted. It just should contain a list of the extracted texts, with no changes made to the text."
n = 20
input_texts = df.plainpagefulltext[:n]
page_ids = df.page_id[:n]


# Die Page-id können wir später verwenden um den extrahierten Text zu den Metadaten die wir in der API
# response erhalten haben zurück zu mappen.
for page_id, input_text in zip(page_ids, input_texts):
    response = model.generate_content([prompt, input_text])
    response = response.text.replace("```python", "").replace("```", "")
    response = ast.literal_eval(response)
    try:
        if response is not None or response == []:
            for r in response:
                results.append((page_id, r))
    except:
        print("Error while appending the output-list!")
    sleep(5)
    
print(results)
print(len(results))

results_df = pd.DataFrame(data={"page_id_plus_texts":results})
results_df.to_csv("page_id_plus_texts.csv", sep=";", index=False)
