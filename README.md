# fp_socss202
### Table of Content
- [get_data_from_ddbapi](#get_data_from_ddbapi)
- [Konzept](#Konzept)
- [deutsches_zeitungs_portal](#deutsches_zeitungs_portal)
- [InformationExtractor](#InformationExtractor)
- [Literatur](#Literatur)
- [Sample](#Sample)
- [Flowchart der InformationExtractor Klasse](#Flowchart)

# deutsches_zeitungs_portal
Das deutsche Zeitungsportal bietet auf seiner <a href = "https://github.com/Deutsche-Digitale-Bibliothek/ddblabs-ddbapi">Internetseite<a> die Möglichkeit eine sehr große Anzahl von historischen Zeitungen zu betrachten. Dabei lässt sich auch eine Schlagwortsuche durchführen. Sucht man nach dem Begriff Heiratsgesuch findet man auf ungefähr 21000 Zeitungsseiten ein Match. 
<p>
<br>
<img width="829" alt="image" src="https://github.com/user-attachments/assets/4fb7c476-bde7-4c8f-a606-92fa6d48f6a5" />
<br>  
</p>
Diese Schlagwortsuche kann nicht nur auf der Website durchgeführt werden, sondern ist auch über eine API zugänglich. Dies ermöglicht es uns auf einem sehr einfachen Weg auf die digitialisierten Texte zuzugreifen und sie in einem für uns sehr einfach nutzbaren Format zu speichern. (Anstatt sehr umständlich mit Selenium einem Scraper zu schreiben).  

# Konzept 
![Flowchart (1)](https://github.com/user-attachments/assets/648587df-31a5-4615-8e21-cce8b77bb24e)



# get_data_from_ddbapi
Dieses Skript verwendet das ddbapi Packet um Daten von der API des deutschen Zeitungsportals zu entnehmen. Relevante Dokumentation zu diesem Paket finden sie <a href = "https://github.com/Deutsche-Digitale-Bibliothek/ddblabs-ddbapi">hier<a>. Das Paket bietet im Grunde nur eine funktion die für die unsere Zwecke relevant ist `zp_pages()`. Sie wird wie folgt angewendent:
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

Da wir eine Art Rate-Limit-Fehler bekommen, wenn wir keinen Ort bei der API-Abfrage angeben, müssen wir durch die möglichen Orte loopen (die Möglichkeiten findet man auf der Webiste der DDB, wenn man einen Suchbegroff eingibt), sodass wir für jeden Ort eine eigene Anfrage stellen - das löst den Rate-Limit-Fehler.


# InformationExtractor
Nachdem die Daten über die API importiert worden sind müssen wir sie jetzt für uns nutzbar machen. Die Texte die wir erhalten haben sind die Volltexte, der Seiten in denen ein Match mit dem Suchwort "Heiratsgesuch" gefunden wurde. Um nun die konkreten Kontaktanzeigen aus diesen Volltexten zu entnehmen verwenden wir die GeminiAPI. An diese senden wir den Volltext und geben explizite Anweisungen wie und welchen Text sie aus dem Volltext extrahieren soll. So erhalten nur die relevanten Stellen aus dem Dokument. 
Das aktuelle Skript `information_extractor_lib` implementiert die Klasse `InformationExtractor`. Diese Klasse bekommt as Input drei Werte:
- `df` - pandas dataframe der die von der ddbapi entnommenen daten enthält
- `page_id_colname` - Spaltename im Dataframe in dem die Page-Ids enthalten sind
- `text_colname` - Spaltenname im Dataframe in dem die Volltexte gespeichert sind.
- `output_path` - Pfad an dem die Ergebnisse der Informationsextraktion gespeichert werden sollen. Im Falle, dass bereits einmal Ergebnisse zwischengespeichert wurden von dieser Klasse - muss kein neuer Pfad angegeben werden. Die Klasse konkatiniert die alten Ergebnisse mit den neuen Ergebnissen (Sofern diese die gleichen Spaltennamen haben).

Um nun den Task der Informationsextraction zu performen werden 5 verschiedene Funktionen der Klasse `information_extractor` durchlaufen:
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
Wenn der config_file im richtigen Format vorliegt und die Daten der ddbapi im Arbeitsverzeichnis vorliegen können wir die Klasse wie folgt anweden:
```py

from scripts.information_extractor_lib import InformationExtractor
import pandas as pd


df = pd.read_csv("newspaper_concat.csv", sep=";")

information_extractor = InformationExtractor(df=df, page_id_colname="page_id", text_colname="plainpagefulltext", output_filename="out_df.csv")
ergebnis_df = information_extractor.extract_data_loop(max_n = 300)
print(ergebnis_df)


```

# Literatur
Folgende Literatur könnte im Kontext dieses Repos interessant sein:
- Schwitter, Nicole (2025): Using large language models for preprocessing and information extraction from unstructured text: A proof-of-concept application in the social sciences, in: Methodological Innovations 18 (1), 61-65.
- Foisy, Laurence-Olivier et al. (2025): Prompting the Machine: Introducing an LLM Data Extraction Method for Social Scientists, in:  Social Science Computer Review 0 (0), S. 1-14.

# Sample

![image](https://github.com/user-attachments/assets/5490c3b3-43ee-450d-9a4f-29a5d12b421c)


# Flowchart der InformationExtractor Klasse


[![](https://mermaid.ink/img/pako:eNp9VGtT2zgU_Ssa7ez0S6CBJBA8bXfybqCERygFHMYjrOtEU1vKyDKEBv776uXEaWc3H5JI99zHOffqrnEsKOAAJ6l4iRdEKnTTn3GkP51wqvQ5QGOeCJkRxQQfrJQksRJyP4oYZyqKHtHe3hfUDcf6xEjKfgEiSkn2VCjIg09P8uOXPZTpHGnESQY1tJQiWypvoIm-IHOIGI1ikTqEgpUqTx4nCrUsVJSwFMzto6vQfXdtBb0QXG0RJYpEqRBLFJM0BerBPQvrh6kglPF5ZAgjWEGsC6U7AfsWOQhzMGXwhM0dj579X0hAncsxOoNX7zWw-KGNHFmqHi-BKEAj4CC1es9wbmzeaWidRs7JlOx8vMBWgxwRTkt5cpRo4VBfI4fydwlGNtjXahMk5EWqUMpy5aFfLWjsuoqMQAFi6DOqIyVQRlYR34k5tvDTjay5Fi2FyJSzK-ypBZ6FsaXrBNDDoftVypY9MQ6-8eiFqQWyZkvSBzmzQb6FXiydQnAFXKHC5EWdsZshj_5m0efhJZE5oNPpxcTwXQqe7-pybnGTMF5A_NNX5kZpl8LE4i7WusOKMJ6Xov_z7uwXxv42EW_oMuzQTU-McC7cYxV3D_kbutoG81TKYJc22ZU7XG0iX9vIFBJi-uZ9nIIfJkItjAyJKPREMI4WIOHDYzWETToNLxw7lqNnPQclv2ubclqVZmqvbmxSPyuazZ9Tc2Nx38NpCrBERygHXRrNvfW7td6uGfobtdBnPUwly9ttVT_K0dBaRTTx0jtqU_IMmpACmQFlpvGuhDLB7Uafu9AIynhRtviHzX0f2hCbd2FY9Ka3HnNvMXdV4nf26kGX_MlNfVnxw7bicfXGJO90_ofDkHGSmvGOITfTujOCnY5bkN21b43ZYXrvaIXzMnO3u03d64XXQKhDmJ5vyXiYqaffD_124fDyx1LouV03GITl27OPzkDNpvGovttzw6FOqArJdWWGx-_BBn69Daushn59jcIBpwHyAbwEQP9jTeXqVXPvGAnS4C84SFoJVC2jkTfFbTiKT6qmvrckSdKAetVyWlpiaEJctUxKSwNaSWunhE0N7aQFbVzDc8koDpQsoIYzPYzEHPHaOM2wWkAGMxzov5TInzM84-_aZ0n4gxBZ6SZFMV_gICFprk_FUksNfUbmWobNrQROQfb0M1Y4ODy2MXCwxiscNJr7J43jZrvZbBzXm_VGs4ZfcdBs7rcP2kcnh-324UFD_7zX8C-btL7fPm69_wuu_nJC?type=png)](https://mermaid.live/edit#pako:eNp9VGtT2zgU_Ssa7ez0S6CBJBA8bXfybqCERygFHMYjrOtEU1vKyDKEBv776uXEaWc3H5JI99zHOffqrnEsKOAAJ6l4iRdEKnTTn3GkP51wqvQ5QGOeCJkRxQQfrJQksRJyP4oYZyqKHtHe3hfUDcf6xEjKfgEiSkn2VCjIg09P8uOXPZTpHGnESQY1tJQiWypvoIm-IHOIGI1ikTqEgpUqTx4nCrUsVJSwFMzto6vQfXdtBb0QXG0RJYpEqRBLFJM0BerBPQvrh6kglPF5ZAgjWEGsC6U7AfsWOQhzMGXwhM0dj579X0hAncsxOoNX7zWw-KGNHFmqHi-BKEAj4CC1es9wbmzeaWidRs7JlOx8vMBWgxwRTkt5cpRo4VBfI4fydwlGNtjXahMk5EWqUMpy5aFfLWjsuoqMQAFi6DOqIyVQRlYR34k5tvDTjay5Fi2FyJSzK-ypBZ6FsaXrBNDDoftVypY9MQ6-8eiFqQWyZkvSBzmzQb6FXiydQnAFXKHC5EWdsZshj_5m0efhJZE5oNPpxcTwXQqe7-pybnGTMF5A_NNX5kZpl8LE4i7WusOKMJ6Xov_z7uwXxv42EW_oMuzQTU-McC7cYxV3D_kbutoG81TKYJc22ZU7XG0iX9vIFBJi-uZ9nIIfJkItjAyJKPREMI4WIOHDYzWETToNLxw7lqNnPQclv2ubclqVZmqvbmxSPyuazZ9Tc2Nx38NpCrBERygHXRrNvfW7td6uGfobtdBnPUwly9ttVT_K0dBaRTTx0jtqU_IMmpACmQFlpvGuhDLB7Uafu9AIynhRtviHzX0f2hCbd2FY9Ka3HnNvMXdV4nf26kGX_MlNfVnxw7bicfXGJO90_ofDkHGSmvGOITfTujOCnY5bkN21b43ZYXrvaIXzMnO3u03d64XXQKhDmJ5vyXiYqaffD_124fDyx1LouV03GITl27OPzkDNpvGovttzw6FOqArJdWWGx-_BBn69Daushn59jcIBpwHyAbwEQP9jTeXqVXPvGAnS4C84SFoJVC2jkTfFbTiKT6qmvrckSdKAetVyWlpiaEJctUxKSwNaSWunhE0N7aQFbVzDc8koDpQsoIYzPYzEHPHaOM2wWkAGMxzov5TInzM84-_aZ0n4gxBZ6SZFMV_gICFprk_FUksNfUbmWobNrQROQfb0M1Y4ODy2MXCwxiscNJr7J43jZrvZbBzXm_VGs4ZfcdBs7rcP2kcnh-324UFD_7zX8C-btL7fPm69_wuu_nJC)
