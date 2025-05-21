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
prompt = configs["PROMPT"]
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
