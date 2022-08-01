#### Pour améliorer le code, regarder
https://github.com/MaximeChallon/AdresseParser/blob/master/AdresseParser/AdresseParser.py
#### Pour MongoDB
https://www.mongodb.com/blog/post/getting-started-with-python-and-mongodb
#### Pour Flask
* https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3-fr

* upload https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask

* download fichier généré : https://www.educative.io/answers/how-to-download-files-in-flask

* suppression du fichier après parsage : https://stackoverflow.com/questions/24612366/delete-an-uploaded-file-after-downloading-it-from-flask

#### Idées
* Match d'une personne va se faire avec  nom/prénom + événements + organisation (on calculera un score) + notice d'autorité.

* Proposer enregistrement fichier sur serveur (filtre:personne décédée avant 1922) et montrer correspondance.

#### Bouts de code

```
lines_note = io.StringIO(evt)
lines_note = lines_note.readlines()
print(lines_note)
```



```
dict_evt = {
                "id_evt": uuid.uuid4().hex,
                "type": line[0],
                "date": line[1],
                "ind_evt": [{"ind": dict_individu, "role": "objet"}]
            }
```



