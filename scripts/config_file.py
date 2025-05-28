configs = {
  "API_KEY" : "API-Key hier in diesen String schreiben",
  "PROMPT":"Your porpouse is it to extract a pre-defined part of the text i will provide you. The text i'll provide you is an ocr read" \
  "historical newspaper. Your task is it to extract the marriage request from the text. A marriage request is defined a person, male or female, stating their interest in finding"
  "a partner for the porpuse of marriage either for themself or for relatives of them in a newspaper." \
  " It is possible that there are more than one in the text" \
  "in this case extract all of them. If you are done, reevaluate your work and check your results. Revavluate if the extracted text is really a marriage request and not some sort of other requst. Return the results in the format of a python list." \
  "The response should be just the text you extracted. It just should contain a list of the extracted texts, with no changes made to the text.",
  "PROMPT2":"You will receive a text extracted from a historical newspaper. The text contains a marriage request. Your task is it to extract the following "
  "information: sex of the respondend, age of the respondend, eduction of the respondend, occupational status of the respondend, description of the desired partner,"
  "answer me in the json-format use the following keys sex_respondend, age__respondend, eduction_respondend, occupation_respondend, description_desired_partner. Please make no assumption in case of no results"
  "for a given information return None. Answer one in german in case you want to cite something - cite the original text.",
  "prompt_ocr_correction":"You are an OCR expert. You are perfect at fixing errors which happen when digitising text. you will be provided a json string."
  "It contains a list of keys with the corresponding texts. Return me the list in the same json format with the same keys, but correct the ocr-errors that occur in the"
  "test. Here is the json string",
  "batch_size":25

}

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
} 
