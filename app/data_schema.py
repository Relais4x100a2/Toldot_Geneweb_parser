class Person:
    def __init__(self, id_person_geneweb, id_person_parser, type_person, source_person, authorityRecord_person, note_person, id_identity,confidence, firstname, surname, othernames):
        self.id_person_geneweb = id_person_geneweb #alphanumeric
        self.id_person_parser = id_person_parser #alphanumeric:UUID
        self.id_identity = id_identity #alphanumeric:UUID (for later merging if relevant)
        self.surname = surname #text [Array]
        self.firstname = firstname #text [Array]
        self.othernames = othernames #text [Array of dictionnary] Nom public, Sobriquet, Alias, Nom Alias, Prénom alias
        self.type_person = type_person #text constraint:[List]
        self.note_person = note_person #text [Array]
        self.source_person = source_person #alphanumeric:id_source [Array]
        self.authorityRecord_person = authorityRecord_person # Array of dictionary {authority: "", record:""}
        self.confidence = confidence #low,medium,high : automatically set based on number of fields fulfilled _RULES TO SET

class Organization:
    def __init__(self, id_person_geneweb, id_person_parser, type_person, source_person, authorityRecord_person, note_person, id_identity):
        self.id_organization_parser = id_organization_parser
        self.id_identity = id_organization
        self.type_organization = typeorganization
        self.name = name #text [Array]
        self.note_organization = note_organization
        self.source_organization = source_organization
        self.authorityRecord_organization = authorityRecord_organization
        self.confidence = confidence


class Event:
    def __init__(self, id_event, type_event, summary_event,date_event, place_event,source_event,actors_event,note_event,authorityRecord_event):
        self.id_event = id_event
        self.type_event = type_event
        self.summary_event = summary_event
        self.date_event = date_event
        self.place_event = place_event
        self.person_event = actors_event
        self.asset_event = actors_event
        self.note_event = note_event
        self.source_event = source_event
        self.authorityRecord_event = authorityRecord_event
        self.confidence = confidence

class Asset:
    #type : immobilier, mobilier, animal
    #authorityRecord_asset
    pass

class Place:
    pass

class Source:
    #type : text, video, sound, image
    #authorityRecord_source
    pass

class Date:
    pass

class Type:
    #Person: homme, femme, organisation,
    #Place: FREE + equivalent wikidata
    #Event:
    #Source:
    #Date : spot or continue
    #Identities/Title : Specific or Free
    #Role:
    pass

class Relation:
    #
    pass

class Place:
    pass

"""
class Entity:
    def __init__(self, id_entity, type_entity, name, note, source, authorityRecord, confidence):
        self.id_entity = id_entity
        self.type_entity = type_entity
        self.name = name
        self.note = note
        self.source = source
        self.authorityRecord = authorityRecord
        self.confidence = confidence

class Person(Entity):
    def __init__(self, id_entity, type_entity, name, note, source, authorityRecord, confidence, firstname, surname, othernames):
        super().__init__(id_entity, type_entity, name, note, source, authorityRecord, confidence)
        self.firstname = firstname
        self.surname = surname
        self.othernames = othernames

class Organization(Entity):
    def __init__(self, id_entity, type_entity, name, note, source, authorityRecord, confidence, type_organization):
        super().__init__(id_entity, type_entity, name, note, source, authorityRecord, confidence)
        self.type_organization = type_organization

class Event(Entity):
    def __init__(self, id_entity, type_entity, name, note, source, authorityRecord, confidence, summary_event, date_event, place_event, actors_event, asset_event):
        super().__init__(id_entity, type_entity, name, note, source, authorityRecord, confidence)
        self.summary_event = summary_event
        self.date_event = date_event
        self.place_event = place_event
        self.actors_event = actors_event
        self.asset_event = asset_event


VARIANTE 

from typing import List, Dict, Union
from enum import Enum

class ConfidenceLevel(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

class Entity:
    """
    Base class for entities such as Person or Organization with common attributes.

    Attributes:
    - id_parser (str): A UUID identifier from the parser.
    - id_identity (str): A UUID for merging identities if relevant.
    - type_entity (str): The type of entity, with constraints.
    - notes (List[str]): Notes associated with the entity.
    - sources (List[str]): A list of source identifiers.
    - authority_records (List[Dict[str, str]]): Authority records for the entity.
    - confidence (ConfidenceLevel): The confidence level of the information.
    """
    def __init__(self, id_parser: str, id_identity: str, type_entity: str, 
                 notes: List[str], sources: List[str], authority_records: List[Dict[str, str]], 
                 confidence: ConfidenceLevel):
        self.id_parser = id_parser
        self.id_identity = id_identity
        self.type_entity = type_entity
        self.notes = notes
        self.sources = sources
        self.authority_records = authority_records
        self.confidence = confidence

class Person(Entity):
    """
    A class to represent a person, inheriting from Entity and adding specific attributes.

    Additional Attributes:
    - firstname (List[str]): A list of first names.
    - surname (List[str]): A list of surnames.
    - othernames (List[Dict[str, str]]): Other names such as public names, aliases, etc.
    """
    def __init__(self, id_person_geneweb: str, firstname: List[str], surname: List[str], 
                 othernames: List[Dict[str, str]], **kwargs):
        super().__init__(**kwargs)
        self.id_person_geneweb = id_person_geneweb
        self.firstname = firstname
        self.surname = surname
        self.othernames = othernames

class Organization(Entity):
    """
    A class to represent an organization, inheriting from Entity and adding specific attributes.

    Additional Attributes:
    - name (List[str]): A list of names for the organization.
    """
    def __init__(self, name: List[str], **kwargs):
        super().__init__(**kwargs)
        self.name = name


"""