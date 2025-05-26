# fp_socss202
### Table of Content
- [get_data_from_ddbapi](#get_data_from_ddbapi)
- [deutsches_zeitungs_portal](#deutsches_zeitungs_portal)
- [information_extractor](#information_extractor)

# deutsches_zeitungs_portal
Das deutsche Zeitungsportal bietet auf seiner <a href = "https://github.com/Deutsche-Digitale-Bibliothek/ddblabs-ddbapi">Internetseite<a> die Möglichkeit eine sehr große Anzahl von historischen Zeitungen zu betrachten. Dabei lässt sich auch eine Schlagwortsuche durchführen. Sucht man nach dem Begriff Heiratsgesuch findet man auf ungefähr 21000 Zeitungsseiten ein Match. 
<p>
<br>
<img width="829" alt="image" src="https://github.com/user-attachments/assets/4fb7c476-bde7-4c8f-a606-92fa6d48f6a5" />
<br>  
</p>
Diese Schlagwortsuche kann nicht nur auf der Website durchgeführt werden, sondern ist auch über eine API zugänglich. Dies ermöglicht es uns auf einem sehr einfachen Weg auf die digitialisierten Texte zuzugreifen und sie in einem für uns sehr einfach nutzbaren Format zu speichern. (Anstatt sehr umständlich mit Selenium einem Scraper zu schreiben).  

# get_data_from_ddbapi
Dieses Skript verwendet das ddbapi Packet um Daten von der API des deutschen Zeitungsportals zu entnehmen. Relevante Dokumentation zu diesem Paket finden sie <a href = "https://github.com/Deutsche-Digitale-Bibliothek/ddblabs-ddbapi">hier<a>. Das Packet bietet im Grunde nur eine funktion die für die unsere Zwecke relevant ist `zp_pages()`. Sie wird wie folgt angewendent:
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


# information_extractor
Nachdem die Daten über die API importiert worden sind müssen wir sie jetzt für uns nutzbar machen. Die Texte die wir erhalten haben sind die Volltexte, der Seiten in denen ein Match mit dem Suchwort "Heiratsgesuch" gefunden wurde. Um nun die konkreten Kontaktanzeigen aus diesen Volltexten zu entnehmen verwenden wir die GeminiAPI. An diese senden wir den Volltext und geben explizite Anweisungen wie und welchen Text sie aus dem Volltext extrahieren soll. So erhalten nur die relevanten Stellen aus dem Dokument. 
Das aktuelle Skript `information_extractor` implementiert die Klasse `information_extractor`. Diese Klasse bekommt as Input drei Werte:
- `input_path` - Pfad zum Datensatz der von der ddbapi gezogen wurde.
- `output_path` - Pfad an dem die Ergebnisse der Informationsextraktion gespeichert werden sollen. Im Falle, dass bereits einmal Ergebnisse zwischengespeichert wurden von dieser Klasse - muss kein neuer Pfad angegeben werden. Die Klasse konkatiniert die alten Ergebnisse mit den neuen Ergebnissen (Sofern diese dien gleichen Spaltennamen haben).
- `model_name` - Gibt den Namen des Gimini-Models an, welches über die API angesprochen werden soll um die Informationen aus den Dokumenten zu entnehmen.

Um nun den Task der Informationsextraction zu performen werden 5 verschiedene Funktionen der Klasse `information_extractor` durchlaufen:
1. `set_config` - setzt den API Key.
2. `load_model` - intialisiert das Model als als Attribut der Klasse. Dabei werden die Model Konfigurationen aus dem config_file geladen.
3. `load_data` - lädt den Dataframe, der unter dem `input_path` abgelegt ist und speichert diesen als Attribut der Klasse ab.
4. `check_output_path` - checkt ob unter dem `output_path` ein File abliegt, wenn nicht wird ein Dataframe im gewünschten Format initialisiert und dort abgelegt.
5. `extract_information` - Kommuniziert mit der API - Es werden iterativ die Volltexte die im Input-dataframe abliegen zusammen mit dem Prompt an die API geschickt. Danach wird die Antwort der API so restrukturiert, dass wir sie weiterverarbeiten können. Die umformatierte Antwort wird dann in Form von Tuplen (page_id, text) in einer Liste abgepeichert, sodass wir diese später in wieder in einem csv-Format unter `output_path` abspeichern können. Die Ergebnisse werden alle 20 Iterationen abgespeichert, sodass wenn es zu unvorhergesehenen Fehlern kommt kein zu großer Datenverlust vorliegt.
6. `information_extraction_flow` Die Funktion information_extraction_flow performt diesen Prozess.

## Anwendung der Klasse
Wenn der config_file im richtigen Format vorliegt und die Daten der ddbapi im Arbeitsverzeichnis vorliegen können wir die Klasse wie folgt anweden:
```py

from information_extractor import information_extractor

if __name__ == "__main__":
    extractor = information_extractor(input_path="newspaper_concat.csv", output_path="page_id_plus_texts.csv", model_name="gemini-1.5-flash")
    extractor.information_extraction_flow()



```

    

# Sample

![image](https://github.com/user-attachments/assets/5490c3b3-43ee-450d-9a4f-29a5d12b421c)


