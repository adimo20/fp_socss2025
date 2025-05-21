# fp_socss202
### Table of Content
- [get_data_from_ddbapi](#get_data_from_ddbapi)
- [deutsches_zeitungs_portal](#deutsches_zeitungs_portal)
- [extract_data_from_fulltext](#extract_data_from_fulltext)

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


# extract_data_from_fulltext
Nachdem die Daten über die API importiert worden sind müssen wir sie jetzt für uns nutzbar machen. Die Texte die wir erhalten haben sind die Volltexte, der Seiten in denen ein Match mit dem Suchwort "Heiratsgesuch" gefunden wurde. Um nun die konkreten Kontaktanzeigen aus diesen Volltexten zu entnehmen verwenden wir die GeminiAPI. An diese senden wir den Volltext und geben explizite Anweisungen wie und welchen Text sie aus dem Volltext extrahieren soll. So erhalten nur die relevanten Stellen aus dem Dokument. 

