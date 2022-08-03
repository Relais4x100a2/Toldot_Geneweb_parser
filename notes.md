#### Pour améliorer le code, regarder
https://github.com/MaximeChallon/AdresseParser/blob/master/AdresseParser/AdresseParser.py

#### Le modèle du fichier geneweb
https://geneweb.tuxfamily.org/wiki/gw/fr

#### Pour Flask
* https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3-fr

* upload https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask

* download fichier généré : https://www.educative.io/answers/how-to-download-files-in-flask

* suppression du fichier après parsage : https://stackoverflow.com/questions/24612366/delete-an-uploaded-file-after-downloading-it-from-flask

#### Pour MongoDB
https://www.mongodb.com/blog/post/getting-started-with-python-and-mongod

#### Idées pour plus tard
* Match d'une personne va se faire avec  nom/prénom 
* + événemenpour plus tardts + organisation (on calculera un score) + notice d'autorité.

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
```
<link rel="stylesheet" href="{{ url_for('static', filename= 'css/style.css') }}">
```


```
# On récupère les témoins
#match_evt = re.findall(regex_evt, m, re.MULTILINE)
#for evt in match_evt:
    lines_evt = evt.split("\n")
    for i in lines_evt:
        if i.startswith("wit"):
            a = i.split()
            wit = a[2] + " " + a[3]
            for i in list_ind:
                if wit == i["id_geneweb"]:
                    ind_wit = i
                    #Il faut relier le wit au bon événement
                    #dict_evt["ind_evt"].append({"ind": ind_wit, "role": "wit"})
                    #list_evt_ind.append(dict_evt)
```
```  
# On récupère les sources.
            for s in range(0, len(line) - 1):#### Pour MongoDB
                dict_source = {}* https://www.mongodb.com/blog/post/getting-started-with-python-and-mongodb
                if line[s] in ["#s", "#bs", "#ds"]:* https://pymongo.readthedocs.io/en/stable/examples/authentication.html
                    #dict_source["type_cible"] = "evt_ind"
                    #dict_source["cible"] = [{"ind": [dict_individu["id_ind"]], "evt": [dict_evt["id_evt"]]}]
                    dict_source["value_source"] = [line[s + 1]]
                    list_evt_ind_source.append(dict_source)
```  
     