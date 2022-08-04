import re
import uuid
import simplejson as json
import pandas as pd
import os

def parse():
    """
    Parse la chaîne mise en paramètre et retourne un dictionnaire
    :param
    :return: dict
    """
    # VARIABLES
    # Listes vides destinées à recevoir l'ensemle des informations parsées.
    list_ind = []
    list_ind_note = []
    list_ind_source = []

    list_evt_ind = []
    list_evt_ind_note = []
    list_evt_ind_source = []

    list_fam = []
    list_fam_note = []
    list_fam_source = []

    list_evt_fam = []
    list_evt_fam_note = []
    list_evt_fam_source = []

    list_relations = []

    # ***REGEX***

    # regex pour les familles
    regex_famille = r"(?s)(?<=^fam )(.*?)(?=^end\n)"

    # regex pour les individus
    regex_individu = r"(?s)(?<=^pevt )(.*?)(?=end pevt)"
    # regex pour les événements
    # fin de la regex (?=^#) pour inclure les notes liées à l'événement
    regex_evt = r"(?s)(?<=^#)(.*?)(?=^#)"

    # Prévoir étape pour renommer le ficier *.gw en *.txt

    # on lit le ficier *.gw converti en *.txt
    with open('pierre.txt', 'rt') as myfile:
        fichier = myfile.read()

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
    #### Il faudra modifier ind_evt en ajoutant le statut dans l'événement.
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
            dict_evt["id_evt"] = uuid.uuid4().hex
            # Type d'événement
            type_evt = line[0].replace("_", " ")
            ####prevoir replace
            dict_evt["type"] = type_evt

            # Date d'événement
            #### RAJOUTER VERIFICATION PRESENCE DATE
            if line[1]:
                if not re.search("#", line[1]):
                    if re.search("\~", line[1]):
                        dict_evt["date"] = {"type": "vers", "value": [line[1].replace("~", "")]}
                    elif re.search("\?", line[1]):
                        dict_evt["date"] = {"type": "peut-être", "value": [line[1].replace("?", "")]}
                    elif re.search("\<", line[1]):
                        dict_evt["date"] = {"type" : "avant", "value": [line[1].replace("<", "")]}
                    elif re.search("\>", line[1]):
                        dict_evt["date"] = {"type":"après", "value": [line[1].replace(">", "")]}
                    elif re.search("\|", line[1]):
                        date_ou = line[1].split("|")
                        dict_evt["date"] = {"type":"ou", "value": [date_ou[0],date_ou[1]]}
                    elif re.search("\.\.", line[1]):
                        date_entre=line[1].split("..")
                        dict_evt["date"] = {"type":"entre", "value": [date_entre[0],date_entre[1]]}
                    else:
                        dict_evt["date"] = {"type":"exact", "value": [line[1]]}
                else:
                    dict_evt["date"] = None
            else:
                dict_evt["date"] = None
            print( dict_evt["date"])


            # Lieu de l'événment
            try:
                if line[2] == '#p':
                    adresse = line[3].split("_-_")
                    if len(adresse) == 1:
                        ville_cp_d_r_p=adresse[0].replace("_", " ")
                        dict_evt["place"] = {"ville_cp_d_r_p": ville_cp_d_r_p, "complement": None}
                    else:
                        ville_cp_d_r_p = adresse[1].replace("_", " ")
                        complement = adresse[0].replace("_", " ")
                        complement = complement.replace(" [", "")
                        complement = complement.replace("]", "")
                        dict_evt["place"] = {"ville_cp_d_r_p": ville_cp_d_r_p, "complement": complement}
            except IndexError:
                pass

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
                    wit = a[2] + " " + a[3]
                    for i in list_ind:
                        if wit == i["id_geneweb"]:
                            wit_id = {"ind": i, "role": "wit"}
                            list_wit.append(wit_id)

                # au(x) éventuelle(s) notes de l'événement.
                elif i.startswith("note "):
                    x = i.replace("note ", '')
                    if x != '':
                        list_note.append(x)

            if list_wit:
                dict_evt["ind_evt"] = ind_evt_sujet + list_wit
            else:
                dict_evt["ind_evt"] = ind_evt_sujet

            if list_note:
                dict_evt["note"] = list_note

            list_evt_ind.append(dict_evt)

    # On récupère toutes les concordances avec la regex pour les familles
    matches = re.findall(regex_famille, fichier, re.MULTILINE)

    for m in matches:
        # on crée la liste des familles, une famille étant définie par un couple d'individu avec éventuellement des
        # enfants.
        dict_organisation = {}
        dict_membre_organisation = {}
        lines = m.split("\n")
        info_fam = lines[0].split()
        M1 = info_fam[0] + " " + info_fam[1]
        for i in list_ind:
            if M1 == i["id_geneweb"]:
                dict_membre_organisation["ind"] = i
                dict_membre_organisation["role"] = "conjoint"
                # print(dict_membre_organisation)

        # line = m.split()
        # id_g = line[0] + " " + line[1]
        # dict_individu["id_geneweb"] = id_g
        dict_organisation["type_org"] = "famille"
        dict_organisation["id_org"] = uuid.uuid4().hex
        dict_organisation["membres_org"] = []
        # conjoint
        # conjointe
        # enfant -h -f)

    # on assemble les listes individus, familles (=organisation)

    # print(list_ind)
    #print(list_evt_ind)

    # normalisation du JSON
    json_evt_ind = json.dumps(list_evt_ind, ignore_nan=True, ensure_ascii=False)

    # export du fichier JSON
    data_export = os.path.join(os.getcwd(), "data_export")
    geneweb_export = "evt_ind_json.json"
    output_file = os.path.join(data_export, geneweb_export)
    with open(output_file, "w") as outfile:
        outfile.write(json_evt_ind)

    # export du fichier CSV
    df = pd.read_json(json_evt_ind, convert_dates=False)
    df.to_csv("data_export/essai.csv")

    """
    # Declare an empty dataframe to append records
    dataframe = pandas.DataFrame()
    record = pandas.json_normalize(json_evt_ind, record_path=['sections','fields'], meta=[['sections','id'],['sections','name'],'_id','id','projectId','silentDocumentWording','name','description','language','created','lastAccessed','lastUpdated','createdBy','lastUpdatedBy'], record_prefix='meta->sections->fields->', meta_prefix='meta->', sep='->', errors='ignore')
    dataframe = pandas.concat((dataframe, record), axis=1)
    """

    #print(df)



    # print(list_evt_ind_note)
    # print(list_evt_ind_source)


if __name__ == '__main__':
    parse()
