from typing import List, Dict, Optional


class Person:
    """
    A class to represent a person with various identifiers and descriptors.

    Attributes:
    -----------
    id_person_geneweb : str
        A unique alphanumeric identifier from the Geneweb system.
    id_person_parser : str
        A unique alphanumeric UUID from the parser system.
    id_identity : str
        A unique alphanumeric UUID for identity merging purposes.
    type_person : str
        The type/category of person from a predefined list.
    note_person : List[str]
        A list of notes pertaining to the person.
    source_person : List[str]
        A list of alphanumeric source IDs related to the person.
    authorityRecord_person : List[Dict[str, str]]
        A list of dictionaries containing authority and record pairs.

    Methods:
    --------
    __str__() -> str:
        Provides a human-readable string representation of the Person object.
    """

    def __init__(
            self,
            id_person_geneweb: str,
            id_person_parser: str,
            type_person: str,
            source_person: List[str],
            authorityRecord_person: List[Dict[str, str]],
            note_person: Optional[List[str]] = None,
            id_identity: Optional[str] = None
    ) -> None:
        self.id_person_geneweb = id_person_geneweb
        self.id_person_parser = id_person_parser
        self.id_identity = id_identity
        self.type_person = type_person
        self.note_person = note_person if note_person is not None else []
        self.source_person = source_person
        self.authorityRecord_person = authorityRecord_person

        # You can add validation here if needed.
        # For example:
        self.validate_type_person()

    def validate_type_person(self):
        allowed_types = ["male","female","unknown","non-binary","transgender","intersex","other"]  # Replace with actual types
        if self.type_person not in allowed_types:
            raise ValueError(f"type_person must be one of {allowed_types}")

    def __str__(self) -> str:
        return (f"Person(ID Geneweb: {self.id_person_geneweb}, "
                f"ID Parser: {self.id_person_parser}, "
                f"Type: {self.type_person}, "
                f"Notes: {self.note_person}, "
                f"Sources: {self.source_person}, "
                f"Authority Records: {self.authorityRecord_person})")


# Example usage:
try:
    person = Person(
        id_person_geneweb="GW123",
        id_person_parser="UUID123",
        type_person="male",
        source_person=["Source1", "Source2"],
        authorityRecord_person=[{"authority": "Auth1", "record": "Record1"}]
    )
    print(person)
except ValueError as e:
    print(e)
