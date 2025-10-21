# fp_socss202
### Table of Content
- [deutsches_zeitungs_portal](#deutsches_zeitungs_portal)
- [Konzept](#konzept)
- [get_data_from_ddbapi](#get_data_from_ddbapi)
- [informationExtractor](#informationExtractor)
- [Validation](#validation)
- [Literatur](#literatur)
- [Sample](#sample)

# Anmerkungen - Ideen für erweiterte Forschungsfrage
Aufgreifen von LLM as a Judge - zunächst kleines Sample an annotierten Beispielen ergänzen und dann ein Few-Shot learning durchführen. Finetuning der Anworten des Modells auf Basis von annotierten Daten. 

- Important add error logging - need to know why the error occoured - was it a rate limit or an other error. 

# Ergänzungen 
 
- Zu dem eigentlichen Prompt sollten wir noch einen System-Prompt Ergänzen, der die Rahmenbedingungen des Models/Agenten festlegt (vgl. Schuler et al. 2025: 15)
- Automatic Prompt Engineering (APE) so wie im Papaer von  Zhou et al. vorgeschlagen und <a href = "https://github.com/keirp/automatic_prompt_engineer">hier</a> in den Code integrieren. 

# deutsches_zeitungs_portal

Das deutsche Zeitungsportal bietet auf seiner <a href = "https://github.com/Deutsche-Digitale-Bibliothek/ddblabs-ddbapi">Internetseite</a> die Möglichkeit eine sehr große Anzahl von historischen Zeitungen zu betrachten. Dabei lässt sich auch eine Schlagwortsuche durchführen. Sucht man nach dem Begriff Heiratsgesuch findet man auf ungefähr 21000 Zeitungsseiten ein Match. 
<p>
<br>
<img width="829" alt="image" src="https://github.com/user-attachments/assets/4fb7c476-bde7-4c8f-a606-92fa6d48f6a5" />
<br>  
</p>
Diese Schlagwortsuche kann nicht nur auf der Website durchgeführt werden, sondern ist auch über eine API zugänglich. Dies ermöglicht es uns auf einem sehr einfachen Weg auf die digitialisierten Texte zuzugreifen und sie in einem für uns sehr einfach nutzbaren Format zu speichern. (Anstatt sehr umständlich mit Selenium einem Scraper zu schreiben).  

# konzept 

![Flowchart (6)](https://github.com/user-attachments/assets/77cfd169-776a-45e9-a2ac-12d2ed723ed3)


# get_data_from_ddbapi
Dieses Skript verwendet das ddbapi Packet um Daten von der API des deutschen Zeitungsportals zu entnehmen. Relevante Dokumentation zu diesem Paket finden sie <a href = "https://github.com/Deutsche-Digitale-Bibliothek/ddblabs-ddbapi">hier</a>. Das Paket bietet im Grunde nur eine funktion die für die unsere Zwecke relevant ist `zp_pages()`. Sie wird wie folgt angewendent:
```py
df = zp_pages(
        publication_date='[1850-01-01T12:00:00Z TO 1980-12-31T12:00:00Z]', 
        place_of_distribution=place, 
        plainpagefulltext=["Heiratsgesuch"]
        )
```
`zp_pages()` nimmt drei Argumente:
- `publication_date` - definiert den Zeitraum für den Zeitungen durchsucht werden sollen
-  `place_of_distribution` - definiert den Veröffentlichungsort der durchsucht werden soll
-  `plainpagefulltext` - definiert den Suchbegriff der für eine Volltextsuche Verwendet werden soll <br>

Da wir eine Art Rate-Limit-Fehler bekommen, wenn wir keinen Ort bei der API-Abfrage angeben, müssen wir durch die möglichen Orte loopen, die im oberen code in einer Liste `place` gespeichert sind (die Möglichkeiten findet man auf der Webiste der DDB, wenn man einen Suchbegroff eingibt), sodass wir für jeden Ort eine eigene Anfrage stellen - das löst den Rate-Limit-Fehler. Unter `plainpagefulltext=["Heiratsgesuch"]` - könnten wir andere Suchbegriffe einsetzen wie beispielsweise "zwecks heirat" oder ähnliches. 


# informationExtractor

![Flowchart (5)](https://github.com/user-attachments/assets/4a6a1b28-022a-4e97-a709-8caa0f81709b)


Nachdem die Daten über die API importiert worden sind müssen wir sie jetzt für uns nutzbar machen. Die Texte die wir erhalten haben sind die Volltexte, der Seiten in denen ein Match mit dem Suchwort "Heiratsgesuch" gefunden wurde. Um nun die konkreten Kontaktanzeigen aus diesen Volltexten zu entnehmen verwenden wir die GeminiAPI. An diese senden wir den Volltext und geben explizite Anweisungen wie und welchen Text sie aus dem Volltext extrahieren soll. So erhalten nur die relevanten Stellen aus dem Dokument. 
Das aktuelle Skript `information_extractor_lib` implementiert die Klasse `InformationExtractor`. Diese Klasse bekommt as Input drei Werte:
- `df` - pandas dataframe der die von der ddbapi entnommenen daten enthält
- `page_id_colname` - Spaltename im Dataframe in dem die Page-Ids enthalten sind
- `text_colname` - Spaltenname im Dataframe in dem die Volltexte gespeichert sind.
- `output_path` - Pfad an dem die Ergebnisse der Informationsextraktion gespeichert werden sollen. Im Falle, dass bereits einmal Ergebnisse zwischengespeichert wurden von dieser Klasse - muss kein neuer Pfad angegeben werden. Die Klasse konkatiniert die alten Ergebnisse mit den neuen Ergebnissen (Sofern diese die gleichen Spaltennamen haben), kann aber auch fürs erste als None gesetzt werden, wenn wir unserer Daten nicht direkt speichern wollen.

Um nun den Task der Informationsextraction zu performen werden verschiedene Funktionen der Klasse `information_extractor` implementiert:
1. `set_config` - setzt den API Key.
2. `load_model` - intialisiert das Model als als Attribut der Klasse. Dabei werden die Model Konfigurationen aus dem config_file geladen.
3. `load_data` - speichert die input texte und die page ids in zwei elementen des init `page_ids` und `input_texts`
4. `loading_flow` - flow der das API-Model lädt und im init unter `model` speichert
5. `create_model_input` - erstellt den Model-Input durch das kombinieren des Prompt der Page Id und des Texts.
6. `check_model_output` - überprüft ob alle nötigen Informationen in geeigneter Form, in der Response enthalten sind. Wenn ja gibt es die Response zurück wenn nicht werden die fehlenden Angaben imputiert, heißt, es wird entweder die page_id ergänzt oder der Text wird als "Not found" geflagt.
7. `extract_single_page` - Kommuniziert mit der API - und extrahiert die im prompt angebenene Information aus dem unstrukturierten Volltext.
8. `create_out_df` - erzeugt einen pandas Dataframe der später unter dem Output path abgelegt wird. 
9. `extract_data_loop` - Es werden iterativ die Volltexte die im Input-dataframe abliegen zusammen mit dem Prompt an die API geschickt.
10. `information_extraction_flow` Die Funktion information_extraction_flow performt diesen Prozess.

## Anwendung der Klasse
Wenn der config_file im richtigen Format vorliegt und die Daten der ddbapi im Arbeitsverzeichnis vorliegen können wir die Klasse wie folgt anweden. Die Klasse ist generisch implementiert. Das heißt wir können mehr als einen task mit ihr ausführen. Sie ist so optimiert, dass wir Informationsextraktion, OCR-Korrektur und Word-Completion mit ihr durchführen können - Für ein Beispiel wie die Klasse für alle drei Tasks verwendet wird - siehe `execute_fullworkflow.ipynb`. 

```py

from scripts.information_extractor_lib import InformationExtractor
import pandas as pd


df = pd.read_csv("newspaper_concat.csv", sep=";")

information_extractor = InformationExtractor(df=df, page_id_colname="page_id", text_colname="plainpagefulltext", output_filename="out_df.csv")
ergebnis_df = information_extractor.extract_data_loop(max_n = 300)
print(ergebnis_df)


```

Der init der Klasse enthält folgendes: 

- `configs` - load the config file that is per default loaded. In there is the prompt and the model to use saved.
- `model_name:str` - if the model in the config needs to changed it can via this attribute. In case this attribute is set the model defined by this name will be used, instead of the one in the config
- `prompt:str` -  if the prompt in the config needs to changed it can via this attribute. In case this attribute is set the prompt defined by this name will be used, instead of the one in the config
- `model:str` - model api is stored here
- `page_ids:list` - list to store the ids of each text entry
-  `input_texts:list` - list to store the original texts that should be processed by the model
- `df:pd.DataFrame` - data-frame from which the page ids and the input-texts are extracted but if I think a little bit - <b> this could be changed - so i don't give the colnames for the text and the ids and the df - instead directly giving the desired inputs as a list. </b>
- `model_input` - prompt and text are concatinated here
- `page_id_colname:str` - colname of pageids in df
- `text_colname:str` - colname of texts in df
- `output_filename:str` - filename for potential output
- `sleeping_time:int` = 4 -  This is critical - because if the model responds to fast too often then this will result in ratelimit errors. 
- `safe_results_external:bool` - determines if output should be directly written - by default false
- `generation_config` - model config generation - critical for reproduction of the results
- `verbose:bool` - if true prints out the extracted contet 
- `save_one_result_per_row:bool` - determines if multiple examples are extracted per one input. So that we need to save more than one result per input 

### Config

Wichtig der Api Key in dieser Art dem Implementierung wird als Umgebungsvariable geladen - hier wird es zu `FEHLERN` kommen. Erkläre ich in der Sitzung 

```py
configs = {
  "API_KEY" : os.environ.get("GEMINI_API_KEY"),
  
  "PROMPT":"Your porpouse is it to extract a pre-defined part of the text i will provide you. The text i'll provide you is an ocr read" \
  "historical newspaper. Your task is it to extract the marriage request from the text. A marriage request is defined a person, male or female, stating their interest in finding"
  "a partner for the porpuse of marriage either for themself or for relatives of them in a newspaper." \
  " It is possible that there are more than one in the text" \
  "in this case extract all of them. If you are done, reevaluate your work and check your results. Revavluate if the extracted text is really a marriage request and not some sort of other requst. Return the results in the format of a python list." \
  "The response should be just the text you extracted. It just should contain a list of the extracted texts, with no changes made to the text.",
  
  "model_name":"gemini-2.0-flash",

}
```

# Validatition

Um die Accuracy der entnommenen Informationen anzuwenden wird die Klasse `ExtractionValidator` implementiert. Diese erhält den extrahierten Text `dst_doc` und das original Dokument aus dem die Informationen entnommen wurden `source_doc`, sowie einen Threshold als Input. Mit der Funktion `calculate_extraction_accuracy`  wird überprüft ob die entnomme Textpassage 1:1 im original Dokument zu finden ist. Falls das nicht der Fall ist wird überprüft ob es eine Textpassage in original Dokument die anhand der Levensteindistance approximativ die gleiche ist. Es kann immer passieren, dass das LLM ein Leerzeichen, Komma etc. ergänzt oder weglässt. Daher sollten sich im original Dokument Passagen finden die eine Levenstein Similiarity von ~0.98 haben. Ist dieser Fall gegeben, sollte der String im Sinn und der synatktischen Struktur der gleiche sein.  `calculate_extraction_accuracy`  returnt die Accuracy der Infromations extraction als tuple. Zur weiteren Veranschaulichung siehe `extraction_quality_control.ipynb`  
<br>

![image](https://github.com/user-attachments/assets/38a9eb22-a113-44c1-8937-25ae8435752c)

Anzuwenden ist die Klasse wie folgt, wobei dat_joined ein Datensatz ist, der die extrahierten Texte in der Variable `text` enthält und den originalen Text in der Variable `plainpagefulltext`.

```py 

dat_joined = pd.read_pickle("dat_joined.pkl")
validation = ExtractionValidator(dst_doc=dat_joined.text.tolist(), source_doc=dat_joined.plainpagefulltext.tolist(), threshold=0.98)
result = validation.calculate_extraction_accuracy()
print(result)

#In case you want to just check one text        
validator = ExtractionValidator(dst_doc=None, source_doc=None, threshold=None)
result2 = validator.find_similiar_sequence(dst_doc=dat_joined.text[0], source_doc=dat_joined.plainpagefulltext[0], threshold=0.98)
print(result2)

```
# Task für WiSe 25/26

1. Code-Review - Remove code that is not 100% nessecary.
2. Test-LLM as a Judge - combined with fewshot finetuning.
3. Collect and evaluate data that has run through the whole process.
4. Prompt-Engeneering - using a Second-LLM for generating prompts, to cut out human bias in prompt generation.
5. Schedule a meeting with expert - (e.g. Nicole Schwitter - see literatur below) - to gain expert knowledge on what to report and how to present results from our research - (maybe also regarding a possible publication)

# Literatur
Folgende Literatur könnte im Kontext dieses Repos interessant sein:
- Schwitter, Nicole (2025): Using large language models for preprocessing and information extraction from unstructured text: A proof-of-concept application in the social sciences, in: Methodological Innovations 18 (1), 61-65.
- Foisy, Laurence-Olivier et al. (2025): Prompting the Machine: Introducing an LLM Data Extraction Method for Social Scientists, in:  Social Science Computer Review 0 (0), S. 1-14.

# Sample

![image](https://github.com/user-attachments/assets/5490c3b3-43ee-450d-9a4f-29a5d12b421c)

