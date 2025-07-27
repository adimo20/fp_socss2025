from scripts.schemes import ExtractedContent
import os
configs = {
  "API_KEY" : os.environ.get("GEMINI_API_KEY"),
  
  "PROMPT":"Your porpouse is it to extract a pre-defined part of the text i will provide you. The text i'll provide you is an ocr read" \
  "historical newspaper. Your task is it to extract the marriage request from the text. A marriage request is defined a person, male or female, stating their interest in finding"
  "a partner for the porpuse of marriage either for themself or for relatives of them in a newspaper." \
  " It is possible that there are more than one in the text" \
  "in this case extract all of them. If you are done, reevaluate your work and check your results. Revavluate if the extracted text is really a marriage request and not some sort of other requst. Return the results in the format of a python list." \
  "The response should be just the text you extracted. It just should contain a list of the extracted texts, with no changes made to the text.",
  
  "model_name":"gemini-2.0-flash-lite",

}

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
    "response_schema": ExtractedContent,

}
