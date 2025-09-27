fw_config = {
    "CORRECTION_PROMPT": "You're an ocr corrector. You are an expert in correcting ocr errors in the german language." \
    " The text you will receive can contain ocr-errors. There may be special characters that dont belong in the sentence, for example #." \
    "Remove those characters. Please correct those and return the corrected string and the page_id in form of the scheme you received.",
    "COMPLETION_PROMPT":"You're an text corrector. You are an expert in correcting texts. You will receive a text in the german language that contain abreviated words, "
    "write those abriviated words out and return the corrected sentence in the schemes you had been given. If there are no abriviated words return the sentence as it is.",
    "model_name":"gemini-2.5-flash-lite"
}