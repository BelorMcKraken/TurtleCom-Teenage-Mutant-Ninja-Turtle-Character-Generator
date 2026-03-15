# app/generators/random_character.py

from __future__ import annotations

import random
from typing import Sequence

from app.rules.random_names import ANIMAL_NAME_POOLS
from app.utils.dice import roll_d100


def roll_attribute_score() -> tuple[int, list[int]]:
    rolls = [random.randint(1, 6) for _ in range(3)]
    total = sum(rolls)
    if total in (16, 17, 18):
        extra = random.randint(1, 6)
        rolls.append(extra)
        total += extra
    return total, rolls


def pick_from_ranges(table: list[tuple[range, str]], roll: int) -> str:
    for value_range, name in table:
        if roll in value_range:
            return name
    return ""


def roll_size_choice() -> tuple[int, str]:
    return random.randint(1, 20), random.choice(["short", "medium", "long"])


def normalize_animal_for_names(animal_label: str) -> str:
    s = (animal_label or "").strip().upper()

    direct = {
        "POND TURTLE": "POND TURTLE",
        "TURTLE": "POND TURTLE",
        "SNAPPING TURTLE": "SNAPPING TURTLE",
        "RAT": "RAT",
        "RABBIT": "RABBIT",
        "RACCOON": "RACCOON",
        "FOX": "FOX",
        "WOLF": "WOLF",
        "DOG": "DOG",
        "CAT": "CAT",
        "ALLIGATOR": "ALLIGATOR",
        "CROCODILE": "CROCODILE",
        "BAT": "BAT",
        "BLACK BEAR": "BEAR",
        "GRIZZLY BEAR": "BEAR",
        "BROWN BEAR": "BEAR",
        "POLAR BEAR": "BEAR",
        "BEAR": "BEAR",
        "SKUNK": "SKUNK",
        "OTTER": "OTTER",
        "AARDVARK": "AARDVARK",
        "FROG": "FROG",
        "TOAD": "TOAD",
        "SALAMANDER": "SALAMANDER",
        "NEWT": "NEWT",
        "AXOLOTL": "AXOLOTL",
        "CHIMPANZEE": "CHIMPANZEE",
        "GORILLA": "GORILLA",
        "ORANGUTAN": "ORANGUTAN",
        "ARMADILLO": "ARMADILLO",
        "BADGER": "BADGER",
        "BEAVER": "BEAVER",
        "BUFFALO": "BUFFALO",
        "BISON": "BISON",
        "CAMEL": "CAMEL",
        "ELEPHANT": "ELEPHANT",
        "BOBCAT": "BOBCAT",
        "LYNX": "LYNX",
        "CHEETAH": "CHEETAH",
        "COUGAR": "COUGAR",
        "JAGUAR": "JAGUAR",
        "LEOPARD": "LEOPARD",
        "LION": "LION",
        "TIGER": "TIGER",
        "GOAT": "GOAT",
        "HIPPOPOTAMUS": "HIPPOPOTAMUS",
        "HORSE": "HORSE",
        "LEMUR": "LEMUR",
        "GECKO": "GECKO",
        "SKINK": "SKINK",
        "CHAMELEON": "CHAMELEON",
        "GILA MONSTER": "GILA MONSTER",
        "IGUANA": "IGUANA",
        "KOMODO DRAGON": "KOMODO DRAGON",
        "MARTEN": "MARTEN",
        "MINK": "MINK",
        "MOLE": "MOLE",
        "MONKEY": "MONKEY",
        "BABOON": "BABOON",
        "MUSKRAT": "MUSKRAT",
        "PIG": "PIG",
        "BOAR": "BOAR",
        "PORCUPINE": "PORCUPINE",
        "OPOSSUM": "OPOSSUM",
        "SHARK": "SHARK",
        "SHEEP": "SHEEP",
        "SQUIRREL": "SQUIRREL",
        "WEASEL": "WEASEL",
        "FERRET": "FERRET",
        "WOLVERINE": "WOLVERINE",
        "MOUSE": "MOUSE",
        "GERBIL": "GERBIL",
        "HAMSTER": "HAMSTER",
        "GUINEA PIG": "GUINEA PIG",
        "PIKA": "PIKA",
    }

    if s in direct:
        return direct[s]

    for key in direct:
        if key in s:
            return direct[key]

    return ""


def random_name_for_animal(animal_label: str) -> str:
    key = normalize_animal_for_names(animal_label)
    pool: Sequence[str] = ANIMAL_NAME_POOLS.get(key, [])
    return random.choice(pool) if pool else ""