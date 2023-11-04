import re
import uuid
import simplejson as json
import pandas as pd
import os
import shutil
from flask import send_file, request, abort, flash, redirect, url_for
from werkzeug.utils import secure_filename



def parse():
    # création du dossier dans lequel seront enregistrés les fihciers ci-dessus
    id = uuid.uuid4().hex
    directory = "toldot_gw_parser_" + id
    parent_dir = "data_export"
    data_export = os.path.join(os.getcwd(), parent_dir, directory)
    data_zip = os.path.join(os.getcwd(), parent_dir, "archive")
    os.makedirs(data_export)

    # uplooad du fichier
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename == '':
        shutil.rmtree(data_export)
        return "Error_1"
    elif filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in ['.gw']:
            shutil.rmtree(data_export)
            return "Error_2"
        uploaded_file.save(os.path.join(data_export, filename))
        os.rename(os.path.join(data_export, filename), os.path.join(data_export, "file.txt"))
        file = os.path.join(data_export, "file.txt")

    # On lit le ficier *.gw converti en *.txt
    with open(file, 'rt') as myfile:
        fichier = myfile.read()

        # VARIABLES
        # Listes vides destinées à recevoir l'ensemle des informations parsées.
        list_ind = []
        list_evt = []
        list_org = []

        # REGEX
        # Pour les individus
        regex_individu = r"(?s)(?<=^pevt )(.*?)(?=end pevt)"
        # Pour les organisations (familles)
        regex_famille = r"(?s)(?<=^fam )(.*?)(?=^end\n|end fevt\nnotes|end fevt\npevt|end fevt\nfam)"
        # Pour les événements (?=^#) pour inclure les notes
        regex_evt = r"(?s)(?<=^#)(.*?)(?=^#|^end fevt)"

        # On identifie tous les individus ayant des "PEVT" (personal event).
        matches_ind = re.findall(regex_individu, fichier, re.MULTILINE)
        # Via une première boucle, on crée une liste des individus,
        # défini sous la forme d'un dictionnaire (id_geneweb + id uuid4)
        for m in matches_ind:
            dict_individu = {}
            line = m.split()
            id_g = line[0] + " " + line[1]
            dict_individu["id_geneweb"] = id_g
            dict_individu["id_ind"] = uuid.uuid4().hex
            list_ind.append(dict_individu)

        # Via une deuxième boucle, on récupère les événements et les notes, sources et témoins liées.
        for m in matches_ind:
            # On relie l'individu à celui dans la liste créée précédement
            lines = m.split("\n")

            ind_evt_s = {}
            info_ind = lines[0].split()
            ind = info_ind[0] + " " + info_ind[1]
            for indidividu in list_ind:
                if ind == indidividu["id_geneweb"]:
                    ind_evt_s = indidividu
            ind_evt_sujet = [{"ind": ind_evt_s, "role": "sujet_objet"}]

            # On crée la liste des événéments de chaque individu, chaque événément étant défini par un dictionnaire
            matches_ind_evt = re.findall(regex_evt, m, re.MULTILINE)
            for evt in matches_ind_evt:
                dict_evt = {}
                line = evt.split()
                dict_evt["evt"] = uuid.uuid4().hex
                # Type d'événement
                type_evt = line[0].replace("_", " ")
                # Note pour plus tard : prévoir également replace pour les événements types geneweb.
                dict_evt["type"] = type_evt

                # Date d'événement
                if indexExists(line, 1) is True:
                    if not re.search("#", line[1]):
                        if re.search("\~", line[1]):
                            dict_evt["date"] = {'type': "vers", 'value': [line[1].replace("~", "")]}
                        elif re.search("\?", line[1]):
                            dict_evt["date"] = {"type": "peut-être", "value": [line[1].replace("?", "")]}
                        elif re.search("\<", line[1]):
                            dict_evt["date"] = {"type": "avant", "value": [line[1].replace("<", "")]}
                        elif re.search("\>", line[1]):
                            dict_evt["date"] = {"type": "après", "value": [line[1].replace(">", "")]}
                        elif re.search("\|", line[1]):
                            date_ou = line[1].split("|")
                            dict_evt["date"] = {"type": "ou", "value": [date_ou[0], date_ou[1]]}
                        elif re.search("\.\.", line[1]):
                            date_entre = line[1].split("..")
                            dict_evt["date"] = {"type": "entre", "value": [date_entre[0], date_entre[1]]}
                        else:
                            dict_evt["date"] = {"type": "exact", "value": [line[1]]}
                    else:
                        dict_evt["date"] = None
                else:
                    dict_evt["date"] = None

                # Lieu de l'événement
                if indexExists(line, 2) is True:
                    for i in range(0, len(line) - 1):
                        if line[i] == '#p':
                            adresse = line[i + 1].split("_-_")
                            if len(adresse) == 1:
                                lieu = adresse[0].replace("_", " ")
                                dict_evt["place"] = {"lieu": lieu, "complement": None}
                            else:
                                lieu = adresse[1].replace("_", " ")
                                complement = adresse[0].replace("_", " ")
                                complement = complement.replace(" [", "")
                                complement = complement.replace("]", "")
                                dict_evt["place"] = {"lieu": lieu, "complement": complement}

                # Les sources de l'événement
                for s in range(0, len(line) - 1):
                    if line[s] in ["#s", "#bs", "#ds"]:
                        dict_evt["source"] = [line[s + 1]]

                # On relie l'événement :
                lines_evt = evt.split("\n")
                list_wit = []
                list_note = []
                # à l'individu sujet_objet de l'événement
                # au(x) éventuel(s) "wit"(s) de l'événement

                for i in lines_evt:
                    if i.startswith("wit"):
                        a = i.split()
                        try:
                            wit = a[2] + " " + a[3]
                            if a[1] == "m:":
                                wit_sex = "h"
                            if a[1] == "f:":
                                wit_sex = "f"
                        except IndexError:
                            wit = a[1] + " " + a[2]
                        for i in list_ind:
                            if wit == i["id_geneweb"]:
                                wit_id = {"ind": i, "role": "wit"}
                                list_wit.append(wit_id)
                                if wit_sex:
                                    i["sexe"] = wit_sex
                    # note pour plus tard si evt avec un type personnalisé (n'appartenant aux types geneweb
                    # et avec plus de 2 témoins - mettre dans une liste org_a_verifier)

                    # au(x) éventuelle(s) notes de l'événement.
                    elif i.startswith("note "):
                        x = i.replace("note ", '')
                        if x != '':
                            list_note.append(x)

                if list_wit:
                    dict_evt["acteur_evt"] = ind_evt_sujet + list_wit
                else:
                    dict_evt["acteur_evt"] = ind_evt_sujet

                if list_note:
                    dict_evt["note"] = list_note

                list_evt.append(dict_evt)

        # On récupère toutes les concordances avec la regex.py pour les familles
        matches_org = re.findall(regex_famille, fichier, re.MULTILINE)

        for m in matches_org:
            # on crée la liste des familles, une famille étant définie par un couple d'individu avec éventuellement des
            # enfants.
            dict_organisation = {}
            list_d = []
            list_d_s = []
            list_of_all_values = [value for elem in list_ind
                                  for value in elem.values()]

            dict_organisation["type_org"] = "famille"
            dict_organisation["id_org"] = uuid.uuid4().hex
            dict_organisation["membres_org"] = []

            lines = m.split("\n")
            info_fam = lines[0].split()
            M1 = info_fam[0] + " " + info_fam[1]

            if len(info_fam) > 2:
                for i in range(1, len(info_fam) - 1):
                    if info_fam[i][0] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                        if info_fam[i + 1][0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                            M2 = info_fam[i] + " " + info_fam[i + 1]

            for i in lines:
                if i.startswith('-') and not i.startswith('--'):
                    desc_line = lines[lines.index(i)]
                    desc_line_split = desc_line.split()
                    if desc_line_split[1] not in ['f', 'h']:
                        d = info_fam[0] + " " + desc_line_split[1]
                        list_d.append(d)
                    else:
                        if indexExists(desc_line_split, 3) is True:
                            # else n'est pas nécessaire au regard du nombre de données (moins de 10) et de leur qualité
                            if not desc_line_split[3].startswith(
                                    ('#', '_(', '?1', '~', '(', '{', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                                d = desc_line_split[3] + " " + desc_line_split[2]
                                list_d.append(d)
                                list_d_s.append((d, desc_line_split[1]))
                            else:
                                d = info_fam[0] + " " + desc_line_split[2]
                                list_d.append(d)
                                list_d_s.append((d, desc_line_split[1]))

            list_of_all_values = [value for elem in list_ind
                                  for value in elem.values()]
            for d in list_d:
                # On rajoute les individus manquants dans la liste list_ind
                dict_individu_2nd = {}
                if d not in list_of_all_values:
                    dict_individu_2nd["id_geneweb"] = d
                    dict_individu_2nd["id_ind"] = uuid.uuid4().hex
                    list_ind.append(dict_individu_2nd)

            for i in list_ind:
                if i["id_geneweb"] == M1:
                    i["sexe"] = 'h'
                    dict_membre_organisation = {}
                    dict_membre_organisation["ind"] = i
                    dict_membre_organisation["role"] = "partenaire"
                    dict_organisation["membres_org"].append(dict_membre_organisation)
                if i["id_geneweb"] == M2:
                    i["sexe"] = 'f'
                    dict_membre_organisation = {}
                    dict_membre_organisation["ind"] = i
                    dict_membre_organisation["role"] = "partenaire"
                    dict_organisation["membres_org"].append(dict_membre_organisation)
                if i["id_geneweb"] in list_d:
                    dict_membre_organisation = {}
                    dict_membre_organisation["ind"] = i
                    dict_membre_organisation["role"] = "enfant"
                    dict_organisation["membres_org"].append(dict_membre_organisation)

            for i in list_d_s:
                # On rajoute le sexe manquants pour les individus de la liste list_ind
                for index in range(len(list_ind)):
                    if list_ind[index]['id_geneweb'] == i[0]:
                        list_ind[index]['sexe'] = i[1]

            dict_organisation["id_lang_naturel"] = M1 + " & " + M2

            # On crée la liste des événéments de chaque famille en tant qu'organisation,
            # chaque événément étant défini par un dictionnaire
            matches_org_evt = re.findall(regex_evt, m, re.MULTILINE)
            for evt in matches_org_evt:
                dict_evt = {}
                line = evt.split()
                dict_evt["evt"] = uuid.uuid4().hex
                # Type d'événement
                type_evt = line[0].replace("_", " ")
                # Note pour plus tard : prévoir également replace pour les événements types geneweb.
                dict_evt["type"] = type_evt

                # Date d'événement
                if indexExists(line, 1):
                    if not re.search("#", line[1]):
                        if re.search("\~", line[1]):
                            dict_evt["date"] = {'type': "vers", 'value': [line[1].replace("~", "")]}
                        elif re.search("\?", line[1]):
                            dict_evt["date"] = {"type": "peut-être", "value": [line[1].replace("?", "")]}
                        elif re.search("\<", line[1]):
                            dict_evt["date"] = {"type": "avant", "value": [line[1].replace("<", "")]}
                        elif re.search("\>", line[1]):
                            dict_evt["date"] = {"type": "après", "value": [line[1].replace(">", "")]}
                        elif re.search("\|", line[1]):
                            date_ou = line[1].split("|")
                            dict_evt["date"] = {"type": "ou", "value": [date_ou[0], date_ou[1]]}
                        elif re.search("\.\.", line[1]):
                            date_entre = line[1].split("..")
                            dict_evt["date"] = {"type": "entre", "value": [date_entre[0], date_entre[1]]}
                        else:
                            dict_evt["date"] = {"type": "exact", "value": [line[1]]}
                    else:
                        dict_evt["date"] = None
                else:
                    dict_evt["date"] = None

                # Lieu de l'événment
                if indexExists(line, 2) is True:
                    for i in range(0, len(line) - 1):
                        if line[i] == '#p':
                            adresse = line[i + 1].split("_-_")
                            if len(adresse) == 1:
                                lieu = adresse[0].replace("_", " ")
                                dict_evt["place"] = {"lieu": lieu, "complement": None}
                            else:
                                lieu = adresse[1].replace("_", " ")
                                complement = adresse[0].replace("_", " ")
                                complement = complement.replace(" [", "")
                                complement = complement.replace("]", "")
                                dict_evt["place"] = {"lieu": lieu, "complement": complement}

                # Les sources de l'événement
                for s in range(0, len(line) - 1):
                    if line[s] in ["#s", "#bs", "#ds"]:
                        dict_evt["source"] = [line[s + 1]]

                # On relie l'événement :
                lines_evt = evt.split("\n")
                list_wit = []
                list_note = []
                # à l'individu sujet_objet de l'événement
                # au(x) éventuel(s) "wit"(s) de l'événement

                for i in lines_evt:
                    if i.startswith("wit"):
                        a = i.split()
                        try:
                            wit = a[2] + " " + a[3]
                            if a[1] == "m:":
                                wit_sex = "h"
                            if a[1] == "f:":
                                wit_sex = "f"
                        except IndexError:
                            wit = a[1] + " " + a[2]
                        for i in list_ind:
                            if wit == i["id_geneweb"]:
                                wit_id = {"ind": i, "role": "wit"}
                                list_wit.append(wit_id)
                                if wit_sex:
                                    i["sexe"] = wit_sex
                    # note pour plus tard si evt avec un type personnalisé (n'appartenant aux types geneweb
                    # et avec plus de 2 témoins - mettre dans une liste org_a_verifier)

                    # au(x) éventuelle(s) notes de l'événement.
                    elif i.startswith("note "):
                        x = i.replace("note ", '')
                        if x != '':
                            list_note.append(x)

                if list_wit:
                    dict_evt["acteur_evt"] = [{"org": {"id_lang_naturel": dict_organisation["id_lang_naturel"],
                                                       "id_org": dict_organisation["id_org"]},
                                               "role": "sujet_objet"}] + list_wit
                else:
                    dict_evt["acteur_evt"] = [{"org": {"id_lang_naturel": dict_organisation["id_lang_naturel"],
                                                       "id_org": dict_organisation["id_org"]}, "role": "sujet_objet"}]

                if list_note:
                    dict_evt["note"] = list_note

                list_evt.append(dict_evt)

            list_org.append(dict_organisation)

    # normalisation du JSON
    json_ind = json.dumps(list_ind, ignore_nan=True, ensure_ascii=False)
    json_org = json.dumps(list_org, ignore_nan=True, ensure_ascii=False)
    json_evt = json.dumps(list_evt, ignore_nan=True, ensure_ascii=False)

    # export du fichier JSON
    geneweb_export_ind = "ind.json"
    geneweb_export_org = "org.json"
    geneweb_export_evt = "evt.json"

    output_file_ind = os.path.join(data_export, geneweb_export_ind)
    output_file_org = os.path.join(data_export, geneweb_export_org)
    output_file_evt = os.path.join(data_export, geneweb_export_evt)

    # export du fichier JSON INDIVIDU
    with open(output_file_ind, "w") as outfile:
        outfile.write(json_ind)
    # export du fichier CSV INDIVIDU
    df = pd.read_json(json_ind, convert_dates=False)
    df.to_csv(data_export + "/csv_ind.csv")

    # export du fichier JSON ORGANISATION (famille)
    with open(output_file_org, "w") as outfile:
        outfile.write(json_org)
    # export du fichier CSV ORGANISATION (famille)
    df = pd.read_json(json_org, convert_dates=False)
    df.to_csv(data_export + "/csv_org.csv")

    # export du fichier JSON EVENEMENT
    with open(output_file_evt, "w") as outfile:
        outfile.write(json_evt)
    # export du fichier CSV EVENEMENT
    df = pd.read_json(json_evt, convert_dates=False)
    df.to_csv(data_export + "/csv_evt.csv")

    filename = "toldot_gw_parser_" + id
    archive = os.path.join(data_zip, filename)

    # création de l'archive
    shutil.make_archive(archive, 'zip', base_dir=data_export)

    # supppresionn des fichiers et du dossier parent
    shutil.rmtree(data_export)

    # envoi de l'archive
    archive_file = archive + '.zip'
    return archive_file


def indexExists(list, index):
    if 0 <= index < len(list):
        return True
    else:
        return False
