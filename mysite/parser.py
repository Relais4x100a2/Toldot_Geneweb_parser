import re
import uuid
import simplejson as json
import pandas as pd
import os
import shutil
from flask import send_file, request, abort, flash, redirect, url_for
from werkzeug.utils import secure_filename

# Helper function to safely extract from regex matches
def get_match_group(match, group_name, default=None):
    try:
        return match.group(group_name)
    except IndexError:
        return default
    except AttributeError: # If match is None
        return default

def parse_date_string(date_str):
    if not date_str or date_str == '0':
        if date_str == '0':
            return {"type": "exact", "value": ["0"], "original": "0"}
        return None

    date_obj = {"type": "exact", "value": [date_str], "original": date_str}
    temp_date_str = date_str

    if temp_date_str.startswith("~"):
        date_obj["type"] = "vers"; temp_date_str = temp_date_str[1:]
    elif temp_date_str.startswith("?"):
        date_obj["type"] = "peut-être"; temp_date_str = temp_date_str[1:]
    elif temp_date_str.startswith("<"):
        date_obj["type"] = "avant"; temp_date_str = temp_date_str[1:]
    elif temp_date_str.startswith(">"):
        date_obj["type"] = "après"; temp_date_str = temp_date_str[1:]

    if ".." in temp_date_str:
        parts = temp_date_str.split("..", 1)
        date_obj["type"] = "entre" if date_obj["type"] == "exact" else date_obj["type"] + "_entre"
        date_obj["value"] = parts
    elif "|" in temp_date_str:
        parts = temp_date_str.split("|", 1)
        date_obj["type"] = "ou" if date_obj["type"] == "exact" else date_obj["type"] + "_ou"
        date_obj["value"] = parts
    else:
        date_obj["value"] = [temp_date_str]

    final_values = []; calendar = None
    for val in date_obj["value"]:
        processed_val = val
        if val.endswith("J"): calendar = "Julien"; processed_val = val[:-1]
        elif val.endswith("F"): calendar = "Français Républicain"; processed_val = val[:-1]
        elif val.endswith("H"): calendar = "Hébreu"; processed_val = val[:-1]
        final_values.append(processed_val)

    date_obj["value"] = final_values
    if calendar: date_obj["calendar"] = calendar

    if date_str.startswith("0(") and date_str.endswith(")"):
        date_obj["type"] = "textuel"; date_obj["value"] = [date_str[2:-1].replace("_", " ")]
        if "calendar" in date_obj: del date_obj["calendar"]

    if not date_obj["value"] or not date_obj["value"][0]:
        if date_obj.get("original") == "0": return {"type": "exact", "value": ["0"], "original": "0"}
        return {"type": "unknown", "original": date_str}
    return date_obj

def parse_person_details_line(line_str):
    details = {}; remaining_line = line_str.strip()
    name_match = re.match(r"^(?P<last_name>(?:[A-ZÀ-ÖØ-Þa-zà-öø-ÿ'-]+_?)+)\s+(?P<first_name>(?:[A-ZÀ-ÖØ-Þa-zà-öø-ÿ'-]+_?)+(?:\.\d+)?)(?:\s|$)", remaining_line)
    if name_match:
        details["id_geneweb_last_name"] = name_match.group("last_name").replace("_", " ")
        first_name_full = name_match.group("first_name").replace("_", " ")
        if "." in first_name_full:
            parts = first_name_full.rsplit('.', 1); details["id_geneweb_first_name"] = parts[0]; details["id_geneweb_number"] = parts[1]
        else: details["id_geneweb_first_name"] = first_name_full
        details["id_geneweb"] = f"{details['id_geneweb_last_name']} {details['id_geneweb_first_name']}"
        if "id_geneweb_number" in details: details["id_geneweb"] += f".{details['id_geneweb_number']}"
        remaining_line = remaining_line[name_match.end():].strip()
    else: return None

    public_name_match = re.match(r"^\((?P<public_name>[^)]+)\)", remaining_line)
    if public_name_match: details["public_name"] = public_name_match.group("public_name").replace("_", " "); remaining_line = remaining_line[public_name_match.end():].strip()
    first_name_alias_match = re.match(r"^\{(?P<first_name_alias>[^}]+)\}", remaining_line)
    if first_name_alias_match: details["first_name_alias"] = first_name_alias_match.group("first_name_alias").replace("_", " "); remaining_line = remaining_line[first_name_alias_match.end():].strip()

    details["titles"] = []
    while True:
        title_match = re.match(r"^\[(?P<title_str>[^\]]+)\]", remaining_line)
        if title_match:
            title_str = title_match.group("title_str"); parts = title_str.split(':', 5)
            title_obj = {"name": parts[0].replace("_", " ") if len(parts) > 0 and parts[0] else None,
                         "title": parts[1].replace("_", " ") if len(parts) > 1 and parts[1] else None,
                         "place": parts[2].replace("_", " ") if len(parts) > 2 and parts[2] else None,
                         "start_date": parse_date_string(parts[3]) if len(parts) > 3 and parts[3] else None,
                         "end_date": parse_date_string(parts[4]) if len(parts) > 4 and parts[4] else None,
                         "nth": parts[5] if len(parts) > 5 and parts[5] else None}
            if title_obj["name"] == "*": title_obj["name"] = "Principal"
            details["titles"].append(title_obj); remaining_line = remaining_line[title_match.end():].strip()
        else: break

    elements = remaining_line.split(); idx = 0; temp_birth_date_str = None; temp_death_date_str = None
    if idx < len(elements) and not elements[idx].startswith("#") and elements[idx] != "!" and not re.match(r"^[kmes?]", elements[idx][0] if elements[idx] else ''):
        temp_birth_date_str = elements[idx]; idx += 1
    if idx < len(elements) and not elements[idx].startswith("#") and elements[idx] != "!" and temp_birth_date_str is not None:
        if re.match(r"^[kmes?]", elements[idx][0] if elements[idx] else ''):
            if (len(elements[idx]) > 1 and elements[idx][1:].strip()) or elements[idx] == "?":
                temp_death_date_str = elements[idx]; idx += 1
        else: temp_death_date_str = elements[idx]; idx += 1

    if temp_birth_date_str: details["birth_data"] = {"date": parse_date_string(temp_birth_date_str)}
    if temp_death_date_str:
        death_type_char = None; actual_death_date_str = temp_death_date_str
        if temp_death_date_str and temp_death_date_str[0] in "kmes" and len(temp_death_date_str) > 1 : death_type_char = temp_death_date_str[0]; actual_death_date_str = temp_death_date_str[1:]
        details["death_data"] = {"date": parse_date_string(actual_death_date_str)}
        if death_type_char: details["death_data"]["type_detail"] = {"k": "killed", "m": "murdered", "e": "executed", "s": "missing"}[death_type_char]

    current_elements_idx = idx
    while current_elements_idx < len(elements):
        elem = elements[current_elements_idx]; next_val_raw = elements[current_elements_idx+1] if current_elements_idx + 1 < len(elements) else None
        next_val = next_val_raw.replace("_", " ") if next_val_raw else None

        if elem == "#nick" and next_val: details["nickname"] = next_val; current_elements_idx += 2
        elif elem == "#salias" and next_val: details["surname_alias"] = next_val; current_elements_idx += 2
        elif elem == "#alias" and next_val: details["alias"] = next_val; current_elements_idx += 2
        elif elem == "#image" and next_val_raw: details["image_path"] = next_val_raw; current_elements_idx += 2
        elif elem == "#occu" and next_val: details["occupation"] = next_val; current_elements_idx += 2
        elif elem == "#src" and next_val: details["person_source"] = next_val; current_elements_idx += 2
        elif elem == "#apubl": details["access"] = "public"; current_elements_idx += 1
        elif elem == "#apriv": details["access"] = "private"; current_elements_idx += 1
        elif elem == "#bp" and next_val: (details.setdefault("birth_data", {}))["place"] = next_val; current_elements_idx += 2
        elif elem == "#bs" and next_val: (details.setdefault("birth_data", {}))["source"] = next_val; current_elements_idx += 2
        elif elem == "!" and next_val_raw: (details.setdefault("baptism_data", {}))["date"] = parse_date_string(next_val_raw); current_elements_idx += 2
        elif elem == "#pp" and next_val: (details.setdefault("baptism_data", {}))["place"] = next_val; current_elements_idx += 2
        elif elem == "#ps" and next_val: (details.setdefault("baptism_data", {}))["source"] = next_val; current_elements_idx += 2
        elif elem == "#od": (details.setdefault("death_data", {}))["obviously_dead"] = True; current_elements_idx += 1
        elif elem == "#mj": (details.setdefault("death_data", {}))["died_young"] = True; (details["death_data"]).setdefault("date", {"type": "died_young", "value": []}); current_elements_idx += 1
        elif elem == "#dp" and next_val: (details.setdefault("death_data", {}))["place"] = next_val; current_elements_idx += 2
        elif elem == "#ds" and next_val: (details.setdefault("death_data", {}))["source"] = next_val; current_elements_idx += 2
        elif elem == "#buri": (details.setdefault("burial_data", {}))["type"] = "burial"; current_elements_idx += 1
            if current_elements_idx < len(elements) and not elements[current_elements_idx].startswith("#"): details["burial_data"]["date"] = parse_date_string(elements[current_elements_idx]); current_elements_idx += 1
        elif elem == "#crem": (details.setdefault("burial_data", {}))["type"] = "cremation"; current_elements_idx += 1
            if current_elements_idx < len(elements) and not elements[current_elements_idx].startswith("#"): details["burial_data"]["date"] = parse_date_string(elements[current_elements_idx]); current_elements_idx += 1
        elif elem == "#rp" and next_val: (details.setdefault("burial_data", {}))["place"] = next_val; current_elements_idx += 2
        elif elem == "#rs" and next_val: (details.setdefault("burial_data", {}))["source"] = next_val; current_elements_idx += 2
        else: current_elements_idx += 1

    if details.get("birth_data", {}).get("date", {}).get("original") == '0':
        if not details.get("death_data", {}).get("date") and not details.get("death_data", {}).get("died_young"):
            (details.setdefault("death_data", {}))["date"] = {"type": "unknown_but_mandatory", "value": []}
    return details

GENEWEB_EVENT_TYPE_MAP = {
    "#birt": "Birth", "#bapt": "Baptism", "#deat": "Death", "#buri": "Burial", "#crem": "Cremation",
    "#acco": "Accomplishment", "#acqu": "Acquisition", "#adhe": "Adhesion", "#bapl": "BaptismLDS",
    "#barm": "BarMitzvah", "#basm": "BatMitzvah", "#bles": "Benediction", "#chgn": "ChangeName",
    "#circ": "Circumcision", "#conf": "Confirmation", "#conl": "ConfirmationLDS", "#degr": "Diploma",
    "#awar": "Decoration", "#demm": "DemobilisationMilitaire", "#dist": "Distinction", "#endl": "Dotation",
    "#dotl": "DotationLDS", "#educ": "Education", "#elec": "Election", "#emig": "Emigration",
    "#exco": "Excommunication", "#flkl": "FamilyLinkLDS", "#fcom": "FirstCommunion", "#fune": "Funeral",
    "#grad": "Graduate", "#hosp": "Hospitalisation", "#illn": "Illness", "#immi": "Immigration",
    "#lpas": "ListePassenger", "#mdis": "MilitaryDistinction", "#mpro": "MilitaryPromotion",
    "#mser": "MilitaryService", "#mobm": "MobilisationMilitaire", "#natu": "Naturalisation",
    "#occu": "OccupationEvent", "#ordn": "Ordination", "#prop": "Property", "#resi": "ResidenceEvent",
    "#reti": "Retired", "#slgc": "ScellentChildLDS", "#slgp": "ScellentParentLDS", "#slgs": "ScellentSpouseLDS",
    "#vteb": "VenteBien", "#will": "Will", "#strng": "StringEvent",
    "#marr": "Marriage", "#nmar": "NoMarriage", "#nmen": "NoMention", "#enga": "Engagement",
    "#div": "Divorce", "#sep": "SeparationEvent", "#anul": "Annulment", "#marb": "MarriageBann",
    "#marc": "MarriageContract", "#marl": "MarriageLicense", "#pacs": "PACS",
    "#cens": "Recensement"
}

def get_standardized_event_type(raw_type):
    return GENEWEB_EVENT_TYPE_MAP.get(raw_type, raw_type.replace("#", "").replace("_", " ").capitalize())

def _parse_pevt_blocks(fichier_content, list_ind_data, list_evt):
    """Parses all pevt blocks from the given file content."""
    regex_pevt_block = r"^pevt\s+(.+)\n((?:.|\n)*?)^end pevt"
    # Use a list to collect matches to avoid altering string during iteration if re.sub is inside loop
    matches = list(re.finditer(regex_pevt_block, fichier_content, re.MULTILINE))
    processed_content = fichier_content

    for match_pevt in matches:
        person_line_str = match_pevt.group(1).strip(); event_block_str = match_pevt.group(2).strip()
        person_base_details = parse_person_details_line(person_line_str)
        if not person_base_details or "id_geneweb" not in person_base_details: continue
        id_g = person_base_details["id_geneweb"]
        if id_g not in list_ind_data: list_ind_data[id_g] = {"id_ind": uuid.uuid4().hex, **person_base_details}
        else:
            for key, value in person_base_details.items():
                if value is not None or key not in list_ind_data[id_g] or list_ind_data[id_g].get(key) is None: list_ind_data[id_g][key] = value
        current_event_data = None
        for line_in_event_block in event_block_str.split('\n'):
            line_strip = line_in_event_block.strip();
            if not line_strip: continue
            if line_strip.startswith("#"):
                if current_event_data: list_evt.append(current_event_data)
                current_event_data = {"evt_id": uuid.uuid4().hex, "acteur_evt": [{"ind_id_geneweb": id_g, "role": "sujet_objet"}]}
                parts = line_strip.split(None, 1); current_event_data["type_raw"] = parts[0]; current_event_data["type"] = get_standardized_event_type(parts[0])
                if len(parts) > 1:
                    event_details_parts = parts[1].split(); el_idx = 0
                    if el_idx < len(event_details_parts) and not event_details_parts[el_idx].startswith("#"): current_event_data["date"] = parse_date_string(event_details_parts[el_idx]); el_idx +=1
                    if el_idx < len(event_details_parts) and event_details_parts[el_idx] == "#p": el_idx +=1
                        if el_idx < len(event_details_parts):
                            place_val = event_details_parts[el_idx]; el_idx += 1
                            while el_idx < len(event_details_parts) and not event_details_parts[el_idx].startswith("#"): place_val += "_" + event_details_parts[el_idx]; el_idx +=1
                            adresse = place_val.split("_-_"); lieu = adresse[0].replace("_", " "); complement = None
                            if len(adresse) > 1: lieu = adresse[1].replace("_", " "); complement = adresse[0].replace("_", " ").replace(" [", "").replace("]", "")
                            current_event_data["place"] = {"lieu": lieu, "complement": complement}
                    if el_idx < len(event_details_parts) and event_details_parts[el_idx] == "#s": el_idx +=1
                        if el_idx < len(event_details_parts):
                            source_val = event_details_parts[el_idx]; el_idx += 1
                            while el_idx < len(event_details_parts) and not event_details_parts[el_idx].startswith("#"): source_val += "_" + event_details_parts[el_idx]; el_idx +=1
                            current_event_data["source"] = [source_val.replace("_", " ")]
            elif line_strip.startswith("wit") and current_event_data:
                wit_parts = line_strip.split(); role_tag = None; sex = None; name_starts_at = 1
                if len(wit_parts) > 1:
                    if wit_parts[1] in ["m:", "f:"]: sex = "h" if wit_parts[1] == "m:" else "f"; name_starts_at = 2
                    elif wit_parts[1].startswith("#"): role_tag = wit_parts[1]; name_starts_at = 2
                        if len(wit_parts) > 2 and wit_parts[2] in ["m:", "f:"]: sex = "h" if wit_parts[2] == "m:" else "f"; name_starts_at = 3
                if len(wit_parts) > name_starts_at:
                    wit_pers_details = parse_person_details_line(" ".join(wit_parts[name_starts_at:]))
                    if wit_pers_details and "id_geneweb" in wit_pers_details:
                        wit_id_g = wit_pers_details["id_geneweb"]
                        if wit_id_g not in list_ind_data: list_ind_data[wit_id_g] = {"id_ind": uuid.uuid4().hex, **wit_pers_details}
                        if sex and list_ind_data[wit_id_g].get("sexe") is None: list_ind_data[wit_id_g]["sexe"] = sex
                        (current_event_data.setdefault("acteur_evt", [])).append({"ind_id_geneweb": wit_id_g, "role": "witness", **({"witness_type": role_tag} if role_tag else {})})
            elif line_strip.startswith("note ") and current_event_data: (current_event_data.setdefault("note", [])).append(line_strip[5:])
        if current_event_data: list_evt.append(current_event_data)
    if matches: # Remove all matched blocks at once after iteration
        processed_content = re.sub(regex_pevt_block, "", processed_content, flags=re.MULTILINE)
    return processed_content

def _parse_fam_blocks(fichier_content, list_ind_data, list_org):
    regex_fam_block_capture = r"^fam\s+([^\n]+)\n?((?:.|\n)*?)(?=\n^fam\s|\n^pevt\s|\n^notes\s|\n^rel\s|\n^page-ext\s|\n^wizard-note\s|\n^notes-db\s|$(?!\n))"
    matches = list(re.finditer(regex_fam_block_capture, fichier_content, re.MULTILINE))
    processed_content = fichier_content
    for match_fam in matches:
        fam_first_line_str = match_fam.group(1).strip(); fam_content_after_first_line = match_fam.group(2).strip() if match_fam.group(2) else ""
        current_org_data = {"id_org": uuid.uuid4().hex, "type_org": "famille", "membres_org": [], "events_org": [], "attributes_org": {}}
        H_id_g, W_id_g = None, None
        fam_parts = fam_first_line_str.split(' + ', 1)
        husband_details = parse_person_details_line(fam_parts[0])
        if husband_details and "id_geneweb" in husband_details: H_id_g = husband_details["id_geneweb"]
            if H_id_g not in list_ind_data: list_ind_data[H_id_g] = {"id_ind": uuid.uuid4().hex, **husband_details}
            else:
                for k,v in husband_details.items():
                    if v is not None or k not in list_ind_data[H_id_g] or list_ind_data[H_id_g].get(k) is None: list_ind_data[H_id_g][k] = v
            if list_ind_data[H_id_g].get("sexe") is None: list_ind_data[H_id_g]["sexe"] = 'h'
            current_org_data["membres_org"].append({"ind_id_geneweb": H_id_g, "role": "partenaire"})

        if len(fam_parts) > 1:
            elements = fam_parts[1].split(); el_idx = 0; wife_name_str_start_idx = 0
            if el_idx < len(elements) and not elements[el_idx].startswith("#") and (elements[el_idx][0].isnumeric() or elements[el_idx][0] in ['~','?','<','>','0']):
                current_org_data["attributes_org"]["wedding_date"] = parse_date_string(elements[el_idx]); el_idx += 1
            wife_name_str_start_idx = el_idx
            while el_idx < len(elements):
                elem = elements[el_idx];
                tag_val_candidate = elements[el_idx+1] if el_idx + 1 < len(elements) else None
                is_next_potential_name_start = False
                if tag_val_candidate and re.match(r"^[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þa-zà-öø-ÿ'-]*_?", tag_val_candidate):
                    if el_idx + 2 < len(elements) and re.match(r"^(?:[A-ZÀ-ÖØ-Þa-zà-öø-ÿ'-]+_?)+(?:\.\d+)?$", elements[el_idx+2]):
                        is_next_potential_name_start = True
                    elif el_idx + 2 > len(elements) : is_next_potential_name_start = True
                    elif el_idx + 1 == len(elements) -1 : is_next_potential_name_start = True
                tag_val = tag_val_candidate if tag_val_candidate and not is_next_potential_name_start else None
                if elem.startswith("#"):
                    if elem == "#mp" and tag_val: current_org_data["attributes_org"]["wedding_place"] = tag_val.replace("_", " "); el_idx += 2
                    elif elem == "#ms" and tag_val: current_org_data["attributes_org"]["wedding_source"] = tag_val.replace("_", " "); el_idx += 2
                    elif elem == "#sep": current_org_data["attributes_org"]["separation_tag"] = True; el_idx += 1
                    elif elem in ["#nm", "#eng", "#nsck", "#nsckm", "#noment", "#banns", "#contract", "#license", "#pacs", "#residence"]:
                        current_org_data["attributes_org"]["relationship_type_tag"] = elem; current_org_data["attributes_org"]["relationship_type"] = get_standardized_event_type(elem); el_idx += 1
                    else: break
                elif elem == "-" and tag_val: current_org_data["attributes_org"]["divorce_date_str"] = tag_val; el_idx += 2
                else: break
                wife_name_str_start_idx = el_idx
            wife_name_segment = " ".join(elements[wife_name_str_start_idx:])
            if wife_name_segment == "? ?": current_org_data["attributes_org"]["wife_unknown"] = True
            elif wife_name_segment:
                wife_details = parse_person_details_line(wife_name_segment)
                if wife_details and "id_geneweb" in wife_details: W_id_g = wife_details["id_geneweb"]
                    if W_id_g not in list_ind_data: list_ind_data[W_id_g] = {"id_ind": uuid.uuid4().hex, **wife_details}
                    else:
                        for k,v in wife_details.items():
                            if v is not None or k not in list_ind_data[W_id_g] or list_ind_data[W_id_g].get(k) is None: list_ind_data[W_id_g][k] = v
                    if list_ind_data[W_id_g].get("sexe") is None: list_ind_data[W_id_g]["sexe"] = 'f'
                    current_org_data["membres_org"].append({"ind_id_geneweb": W_id_g, "role": "partenaire"})
        current_org_data["id_lang_naturel"] = f"{H_id_g or 'Unknown'} & {W_id_g or 'Unknown'}"
        children_block_str_match = re.search(r"^beg\n((?:.|\n)*?)^end", fam_content_after_first_line, re.MULTILINE)
        fevt_block_match = re.search(r"^(fevt\s+[^\n]+\n(?:.|\n)*?^end fevt)", fam_content_after_first_line, re.MULTILINE)
        for line_fam_detail in fam_content_after_first_line.split('\n'):
            line_strip = line_fam_detail.strip()
            if not line_strip or line_strip == "beg" or line_strip == "end" or (fevt_block_match and line_strip.startswith("fevt")) or (fevt_block_match and line_strip == "end fevt") : continue
            if children_block_str_match and line_strip in children_block_str_match.group(1): continue
            if fevt_block_match and line_strip in fevt_block_match.group(1): continue
            if line_strip.startswith("src "): current_org_data["attributes_org"]["family_source"] = line_strip[4:].replace("_"," ")
            elif line_strip.startswith("comm "): current_org_data["attributes_org"]["family_comment"] = line_strip[5:]
            elif line_strip.startswith("cbp "): current_org_data["attributes_org"]["common_children_birth_place"] = line_strip[4:].replace("_"," ")
            elif line_strip.startswith("csrc "): current_org_data["attributes_org"]["common_children_source"] = line_strip[5:].replace("_"," ")
            elif line_strip.startswith("wit"):
                wit_parts = line_strip.split(); role_tag = None; sex = None; name_starts_at = 1
                if wit_parts[0].endswith(':'): name_starts_at = 1
                elif len(wit_parts) > 1 :
                    if wit_parts[1] in ["m:", "f:"]: sex = "h" if wit_parts[1] == "m:" else "f"; name_starts_at = 2
                    elif wit_parts[1].startswith("#"): role_tag = wit_parts[1]; name_starts_at = 2
                        if len(wit_parts) > 2 and wit_parts[2] in ["m:", "f:"]: sex = "h" if wit_parts[2] == "m:" else "f"; name_starts_at = 3
                if len(wit_parts) > name_starts_at :
                    fam_wit_details = parse_person_details_line(" ".join(wit_parts[name_starts_at:]))
                    if fam_wit_details and "id_geneweb" in fam_wit_details:
                        fam_wit_id_g = fam_wit_details["id_geneweb"]
                        if fam_wit_id_g not in list_ind_data: list_ind_data[fam_wit_id_g] = {"id_ind": uuid.uuid4().hex, **fam_wit_details}
                        if sex and list_ind_data[fam_wit_id_g].get("sexe") is None: list_ind_data[fam_wit_id_g]["sexe"] = sex
                        (current_org_data["attributes_org"].setdefault("family_witnesses", [])).append({"ind_id_geneweb": fam_wit_id_g, "role": "family_witness", **({"witness_type": role_tag} if role_tag else {})})
        if children_block_str_match:
            for child_line_str in children_block_str_match.group(1).split('\n'):
                child_line_strip = child_line_str.strip()
                if not child_line_strip.startswith("- "): continue
                child_info_segment = child_line_strip[2:].strip(); child_sex = None
                parts = child_info_segment.split(None, 1)
                if parts[0] in ['h', 'f', '?']: child_sex = parts[0] if parts[0] != '?' else None; child_info_segment = parts[1] if len(parts) > 1 else ""
                child_details_to_parse = child_info_segment
                if H_id_g and list_ind_data[H_id_g].get("id_geneweb_last_name"):
                    temp_parsed = parse_person_details_line(child_info_segment)
                    if not temp_parsed or not temp_parsed.get("id_geneweb_last_name") or \
                       (temp_parsed.get("id_geneweb_last_name") and temp_parsed.get("id_geneweb_first_name") and temp_parsed.get("id_geneweb_last_name") == temp_parsed.get("id_geneweb_first_name")):
                        child_details_to_parse = list_ind_data[H_id_g]["id_geneweb_last_name"] + " " + child_info_segment
                child_details = parse_person_details_line(child_details_to_parse)
                if child_details and "id_geneweb" in child_details: C_id_g = child_details["id_geneweb"]
                    if C_id_g not in list_ind_data: list_ind_data[C_id_g] = {"id_ind": uuid.uuid4().hex, **child_details}
                    else:
                        for k,v in child_details.items():
                            if v is not None or k not in list_ind_data[C_id_g] or list_ind_data[C_id_g].get(k) is None: list_ind_data[C_id_g][k] = v
                    if child_sex and list_ind_data[C_id_g].get("sexe") is None: list_ind_data[C_id_g]["sexe"] = child_sex
                    current_org_data["membres_org"].append({"ind_id_geneweb": C_id_g, "role": "enfant"})
        if fevt_block_match:
            fevt_block_content = fevt_block_match.group(1); actual_event_lines_in_fevt = "\n".join(fevt_block_content.split('\n')[1:-1])
            current_fam_event_data = None
            for line_in_fevt_block in actual_event_lines_in_fevt.split('\n'):
                line_strip = line_in_fevt_block.strip()
                if not line_strip: continue
                if line_strip.startswith("#"):
                    if current_fam_event_data: current_org_data["events_org"].append(current_fam_event_data)
                    current_fam_event_data = {"evt_id": uuid.uuid4().hex, "acteur_evt": [{"org_id": current_org_data["id_org"], "role": "sujet_objet"}]}
                    parts = line_strip.split(None, 1); current_fam_event_data["type_raw"] = parts[0]; current_fam_event_data["type"] = get_standardized_event_type(parts[0])
                    if len(parts) > 1:
                        event_details_parts = parts[1].split(); el_idx = 0
                        if el_idx < len(event_details_parts) and not event_details_parts[el_idx].startswith("#"): current_fam_event_data["date"] = parse_date_string(event_details_parts[el_idx]); el_idx +=1
                        if el_idx < len(event_details_parts) and event_details_parts[el_idx] == "#p": el_idx +=1
                            if el_idx < len(event_details_parts):
                                place_val = event_details_parts[el_idx]; el_idx += 1
                                while el_idx < len(event_details_parts) and not event_details_parts[el_idx].startswith("#"): place_val += "_" + event_details_parts[el_idx]; el_idx +=1
                                adresse = place_val.split("_-_"); lieu = adresse[0].replace("_", " "); complement = None
                                if len(adresse) > 1: lieu = adresse[1].replace("_", " "); complement = adresse[0].replace("_", " ").replace(" [", "").replace("]", "")
                                current_fam_event_data["place"] = {"lieu": lieu, "complement": complement}
                        if el_idx < len(event_details_parts) and event_details_parts[el_idx] == "#s": el_idx +=1
                            if el_idx < len(event_details_parts):
                                source_val = event_details_parts[el_idx]; el_idx += 1
                                while el_idx < len(event_details_parts) and not event_details_parts[el_idx].startswith("#"): source_val += "_" + event_details_parts[el_idx]; el_idx +=1
                                current_fam_event_data["source"] = [source_val.replace("_", " ")]
                elif line_strip.startswith("wit") and current_fam_event_data:
                    wit_parts = line_strip.split(); role_tag = None; sex = None; name_starts_at = 1
                    if len(wit_parts) > 1:
                        if wit_parts[1] in ["m:", "f:"]: sex = "h" if wit_parts[1] == "m:" else "f"; name_starts_at = 2
                        elif wit_parts[1].startswith("#"): role_tag = wit_parts[1]; name_starts_at = 2
                            if len(wit_parts) > 2 and wit_parts[2] in ["m:", "f:"]: sex = "h" if wit_parts[2] == "m:" else "f"; name_starts_at = 3
                    if len(wit_parts) > name_starts_at:
                        fam_evt_wit_details = parse_person_details_line(" ".join(wit_parts[name_starts_at:]))
                        if fam_evt_wit_details and "id_geneweb" in fam_evt_wit_details:
                            wit_id_g = fam_evt_wit_details["id_geneweb"]
                            if wit_id_g not in list_ind_data: list_ind_data[wit_id_g] = {"id_ind": uuid.uuid4().hex, **fam_evt_wit_details}
                            if sex and list_ind_data[wit_id_g].get("sexe") is None: list_ind_data[wit_id_g]["sexe"] = sex
                            (current_fam_event_data.setdefault("acteur_evt", [])).append({"ind_id_geneweb": wit_id_g, "role": "witness", **({"witness_type": role_tag} if role_tag else {})})
                elif line_strip.startswith("note ") and current_fam_event_data: (current_fam_event_data.setdefault("note", [])).append(line_strip[5:])
            if current_fam_event_data: current_org_data["events_org"].append(current_fam_event_data)
        has_explicit_marriage_event = any(evt.get("type") == "Marriage" and evt.get("acteur_evt")[0].get("org_id") == current_org_data["id_org"] for evt in current_org_data["events_org"])
        if not has_explicit_marriage_event and current_org_data["attributes_org"].get("wedding_date"):
            marriage_event = {"evt_id": uuid.uuid4().hex, "type": "Marriage", "type_raw": "#marr_implicit", "date": current_org_data["attributes_org"]["wedding_date"],
                              "place": {"lieu": current_org_data["attributes_org"].get("wedding_place"), "complement": None} if current_org_data["attributes_org"].get("wedding_place") else None,
                              "source": [current_org_data["attributes_org"]["wedding_source"]] if current_org_data["attributes_org"].get("wedding_source") else None,
                              "acteur_evt": [{"org_id": current_org_data["id_org"], "role": "sujet_objet"}]}
            if H_id_g: marriage_event["acteur_evt"].append({"ind_id_geneweb": H_id_g, "role": "partner"})
            if W_id_g: marriage_event["acteur_evt"].append({"ind_id_geneweb": W_id_g, "role": "partner"})
            current_org_data["events_org"].append(marriage_event)
        has_explicit_divorce_event = any(evt.get("type") == "Divorce" and evt.get("acteur_evt")[0].get("org_id") == current_org_data["id_org"] for evt in current_org_data["events_org"])
        if not has_explicit_divorce_event and current_org_data["attributes_org"].get("divorce_date_str"):
            divorce_event = {"evt_id": uuid.uuid4().hex, "type": "Divorce", "type_raw": "#div_implicit", "date": parse_date_string(current_org_data["attributes_org"]["divorce_date_str"]),
                             "acteur_evt": [{"org_id": current_org_data["id_org"], "role": "sujet_objet"}]}
            if H_id_g: divorce_event["acteur_evt"].append({"ind_id_geneweb": H_id_g, "role": "partner"})
            if W_id_g: divorce_event["acteur_evt"].append({"ind_id_geneweb": W_id_g, "role": "partner"})
            current_org_data["events_org"].append(divorce_event)
        if current_org_data["membres_org"]: list_org.append(current_org_data)
    if matches:
        processed_content = re.sub(regex_fam_block_capture, "", processed_content, flags=re.MULTILINE)
    return processed_content

def _parse_notes_blocks(fichier_content, list_ind_data):
    regex_notes_block = r"^notes\s+([^\n]+)\n^beg\n((?:.|\n)*?)^end notes"
    matches = list(re.finditer(regex_notes_block, fichier_content, re.MULTILINE))
    processed_content = fichier_content
    for match_notes in matches:
        person_str = match_notes.group(1).strip(); note_content = match_notes.group(2).strip()
        note_person_details = parse_person_details_line(person_str)
        if note_person_details and "id_geneweb" in note_person_details:
            p_id_g = note_person_details["id_geneweb"]
            if p_id_g in list_ind_data:
                (list_ind_data[p_id_g].setdefault("notes_general", [])).append(note_content)
    if matches:
        processed_content = re.sub(regex_notes_block, "", processed_content, flags=re.MULTILINE)
    return processed_content

def _parse_rel_blocks(fichier_content, list_ind_data, list_evt):
    regex_rel_block = r"^rel\s+([^\n]+)\n^beg\n((?:.|\n)*?)^end(?:[\s\n]|$)"
    matches = list(re.finditer(regex_rel_block, fichier_content, re.MULTILINE))
    processed_content = fichier_content
    for match_rel in matches:
        person_str = match_rel.group(1).strip(); relations_content = match_rel.group(2).strip()
        rel_person_details = parse_person_details_line(person_str)
        if not rel_person_details or "id_geneweb" not in rel_person_details: continue
        subject_person_id_g = rel_person_details["id_geneweb"]
        if subject_person_id_g not in list_ind_data: list_ind_data[subject_person_id_g] = {"id_ind": uuid.uuid4().hex, **rel_person_details}
        for rel_line in relations_content.split('\n'):
            rel_line_strip = rel_line.strip()
            if not rel_line_strip.startswith("- "): continue
            parts = rel_line_strip[2:].split(': ', 1);
            if len(parts) < 2: continue
            rel_type_full = parts[0]; related_persons_str = parts[1]
            rel_event_type_raw = rel_type_full.split(' ')[0]; rel_event_type = f"relationship_{rel_event_type_raw}"
            rel_specifier = rel_type_full.split(' ')[1] if ' ' in rel_type_full else None
            rel_event = {"evt_id": uuid.uuid4().hex, "type_raw": f"-{rel_event_type_raw}", "type": rel_event_type, "acteur_evt": [{"ind_id_geneweb": subject_person_id_g, "role": "subject"}]}
            if rel_specifier: rel_event["relationship_specifier"] = rel_specifier
            role_map = {"fath": f"{rel_event_type_raw}_father", "moth": f"{rel_event_type_raw}_mother"}
            role1_default = f"{rel_event_type_raw}_parent1" if rel_event_type_raw in ["adop", "godp", "fost", "reco", "cand"] else f"{rel_event_type_raw}_related1"
            role2_default = f"{rel_event_type_raw}_parent2" if rel_event_type_raw in ["adop", "godp", "fost", "reco", "cand"] else f"{rel_event_type_raw}_related2"
            if ' + ' in related_persons_str:
                p1_str, p2_str = [p.strip() for p in related_persons_str.split(' + ', 1)]
                p1_details = parse_person_details_line(p1_str)
                if p1_details and "id_geneweb" in p1_details: p1_id_g = p1_details["id_geneweb"]
                    if p1_id_g not in list_ind_data: list_ind_data[p1_id_g] = {"id_ind": uuid.uuid4().hex, **p1_details}
                    role1 = role_map.get("fath") if "fath" in rel_type_full else (role_map.get("moth") if "moth" in rel_type_full and not p2_str else role1_default)
                    rel_event["acteur_evt"].append({"ind_id_geneweb": p1_id_g, "role": role1})
                p2_details = parse_person_details_line(p2_str)
                if p2_details and "id_geneweb" in p2_details: p2_id_g = p2_details["id_geneweb"]
                    if p2_id_g not in list_ind_data: list_ind_data[p2_id_g] = {"id_ind": uuid.uuid4().hex, **p2_details}
                    role2 = role_map.get("moth") if "moth" in rel_type_full else role2_default
                    rel_event["acteur_evt"].append({"ind_id_geneweb": p2_id_g, "role": role2})
            else:
                single_p_details = parse_person_details_line(related_persons_str)
                if single_p_details and "id_geneweb" in single_p_details:
                    single_p_id_g = single_p_details["id_geneweb"]
                    if single_p_id_g not in list_ind_data: list_ind_data[single_p_id_g] = {"id_ind": uuid.uuid4().hex, **single_p_details}
                    role_single = role_map.get(rel_specifier, f"{rel_event_type_raw}_{rel_specifier or 'related'}")
                    rel_event["acteur_evt"].append({"ind_id_geneweb": single_p_id_g, "role": role_single})
            list_evt.append(rel_event)
    if matches:
        processed_content = re.sub(regex_rel_block, "", processed_content, flags=re.MULTILINE)
    return processed_content

def parse():
    id = uuid.uuid4().hex; directory = "toldot_gw_parser_" + id; parent_dir = "data_export"
    data_export = os.path.join(os.getcwd(), parent_dir, directory); data_zip = os.path.join(os.getcwd(), parent_dir, "archive"); os.makedirs(data_export)
    uploaded_file = request.files['file']; filename = secure_filename(uploaded_file.filename)
    if not filename: shutil.rmtree(data_export); return "Error_1"
    file_ext = os.path.splitext(filename)[1]
    if file_ext not in ['.gw']: shutil.rmtree(data_export); return "Error_2"
    uploaded_file.save(os.path.join(data_export, filename)); os.rename(os.path.join(data_export, filename), os.path.join(data_export, "file.txt"))
    file_path = os.path.join(data_export, "file.txt")

    file_encoding = 'iso-8859-1'
    try:
        with open(file_path, 'r', encoding='utf-8') as f_test:
            if 'encoding: utf-8' in f_test.readline().lower(): file_encoding = 'utf-8'
            f_test.read()
    except UnicodeDecodeError: file_encoding = 'iso-8859-1'
    except Exception: pass
    with open(file_path, 'rt', encoding=file_encoding) as myfile: fichier_content = myfile.read()

    list_ind_data = {}; list_evt = []; list_org = []
    database_notes_content = None

    regex_notes_db_block = r"^notes-db\n((?:.|\n)*?)^end notes-db"
    match_notes_db = re.search(regex_notes_db_block, fichier_content, re.MULTILINE)
    if match_notes_db:
        database_notes_content = match_notes_db.group(1).strip()
        fichier_content = fichier_content.replace(match_notes_db.group(0), "", 1)

    fichier_content = _parse_pevt_blocks(fichier_content, list_ind_data, list_evt)
    fichier_content = _parse_fam_blocks(fichier_content, list_ind_data, list_org)
    fichier_content = _parse_notes_blocks(fichier_content, list_ind_data)
    fichier_content = _parse_rel_blocks(fichier_content, list_ind_data, list_evt)

    all_events = list(list_evt)
    for org_data in list_org:
        if "events_org" in org_data:
            all_events.extend(org_data.pop("events_org"))
            if "divorce_date_str" in org_data["attributes_org"]: del org_data["attributes_org"]["divorce_date_str"]
            if "separation_tag" in org_data["attributes_org"]: del org_data["attributes_org"]["separation_tag"]
    list_ind = list(list_ind_data.values())

    for item_list_container in [all_events, list_org]:
        for item in item_list_container:
            actor_lists_keys = []
            if "acteur_evt" in item: actor_lists_keys.append("acteur_evt")
            if "membres_org" in item: actor_lists_keys.append("membres_org")
            if isinstance(item, dict) and "attributes_org" in item and "family_witnesses" in item["attributes_org"]: actor_lists_keys.append("family_witnesses")
            for key_of_list in actor_lists_keys:
                actual_list_to_process = item[key_of_list] if key_of_list != "family_witnesses" else item["attributes_org"]["family_witnesses"]
                for actor_like_obj in actual_list_to_process:
                    if "ind_id_geneweb" in actor_like_obj:
                        actor_geneweb_id = actor_like_obj.pop("ind_id_geneweb")
                        actor_like_obj["ind"] = {"id_ind": list_ind_data.get(actor_geneweb_id, {}).get("id_ind"), "id_geneweb": actor_geneweb_id }
                        if not list_ind_data.get(actor_geneweb_id): actor_like_obj["ind"]["error"] = "Individual not found"
                    if "org_id" in actor_like_obj : actor_like_obj["org"] = {"id_org": actor_like_obj.pop("org_id")}

    if database_notes_content:
        with open(os.path.join(data_export, "metadata.json"), "w", encoding='utf-8') as metafile:
            json.dump({"database_notes": database_notes_content}, metafile, ensure_ascii=False, indent=2)

    json_ind = json.dumps(list_ind, ignore_nan=True, ensure_ascii=False, indent=2)
    json_org = json.dumps(list_org, ignore_nan=True, ensure_ascii=False, indent=2)
    json_evt = json.dumps(all_events, ignore_nan=True, ensure_ascii=False, indent=2)

    geneweb_export_ind = "ind.json"; geneweb_export_org = "org.json"; geneweb_export_evt = "evt.json"
    output_file_ind = os.path.join(data_export, geneweb_export_ind); output_file_org = os.path.join(data_export, geneweb_export_org); output_file_evt = os.path.join(data_export, geneweb_export_evt)
    with open(output_file_ind, "w", encoding='utf-8') as outfile: outfile.write(json_ind)
    pd.read_json(json_ind, convert_dates=False).to_csv(os.path.join(data_export, "csv_ind.csv"), index=False)
    with open(output_file_org, "w", encoding='utf-8') as outfile: outfile.write(json_org)
    pd.read_json(json_org, convert_dates=False).to_csv(os.path.join(data_export, "csv_org.csv"), index=False)
    with open(output_file_evt, "w", encoding='utf-8') as outfile: outfile.write(json_evt)
    pd.read_json(json_evt, convert_dates=False).to_csv(os.path.join(data_export, "csv_evt.csv"), index=False)

    filename_zip = "toldot_gw_parser_" + id; archive_base_path = os.path.join(data_zip, filename_zip)
    shutil.make_archive(archive_base_path, 'zip', root_dir=data_export); shutil.rmtree(data_export)
    return archive_base_path + '.zip'

def indexExists(list_obj, index): return 0 <= index < len(list_obj)

# Flask app for local testing can be added here if needed.
# ...
