import json
import sys
import csv
import re
import logging

from itertools import chain
from functools import partial

logger = logging.Logger(__name__)


def attribute_names(lines):
    # TODO:
    # struct_name_pattern = r"#### (\w+)\n"
    # endpoint_pattern = r"### GET api/v2/([\w-]+)/"

    # e.g. | id         | The identifier for this item pocket resource                    | integer |
    row_pattern = r"\|([^\|]+)\|([^\|]+)\|([^\|]+)\|"

    basic_type_pattern = r"integer|string|boolean"

    # e.g. [EvolutionDetail](#evolutiondetail)
    user_type_pattern = r"\[(\w+)\]\(#[-\w]+\)"

    # e.g. [NamedAPIResource](#namedapiresource) ([BerryFlavor](#berry-flavors))
    parameterized_pattern = r"\[(\w+)\]\(#\w+\) \(\[(\w+)\]\(#[-\w]+\)\)"

    # e.g. list [Name](#resourcename)
    list_pattern = r"list \[(\w+)\]\(#[-\w]+\)"

    # e.g. list [NamedAPIResource](#namedapiresource) ([PokemonSpecies](#pokemon-species))
    parameterized_list_pattern = r"list \[(\w+)\]\(#\w+\) \(\[(\w+)\]\(#[-\w]+\)\)"

    result = []

    for line in lines:
        row_match = re.match(row_pattern, line)
        if not row_match:
            # logger.warning(line)
            continue

        # header = "| Name | Description | Data Type |"
        h_line = "| ---- | ----------- | --------- |"
        h_line_1 = "| ------- | ----------- | --------- |"

        # One (1) exception, where column 0 is wider.
        # | ------- | ----------- | --------- |
        # TODO: Issue for pokeapi.

        whole = row_match.group(0)
        if "Description" in whole or whole == h_line or whole == h_line_1:
            # logger.warning(line)
            continue

        name = row_match.group(1).strip()
        prose = row_match.group(2).strip()
        type_info = row_match.group(3).strip()

        swift_type = None

        basic_type_match = re.match(basic_type_pattern, type_info)
        if basic_type_match:
            basic_type = basic_type_match.group(0)
            if basic_type == "boolean":
                swift_type = "Bool"
            elif basic_type == "integer":
                swift_type = "Int"
            elif basic_type == "string":
                swift_type = "String"

        # One (1) occurence
        basic_type_list_match = re.match(r"list integer", type_info)
        if basic_type_list_match:
            swift_type = "[Int]"

        user_type_match = re.match(user_type_pattern, type_info)
        if user_type_match:
            swift_type = user_type_match.group(1)

        parameterized_match = re.match(parameterized_pattern, type_info)
        if parameterized_match:
            outer = parameterized_match.group(1)
            inner = parameterized_match.group(2)

            swift_type = f"{outer}<{inner}>"

        parameterized_list_match = re.match(parameterized_list_pattern, type_info)
        if parameterized_list_match:
            outer = parameterized_list_match.group(1)
            inner = parameterized_list_match.group(2)

            swift_type = f"[{outer}<{inner}>]"

        list_match = re.match(list_pattern, type_info)
        if list_match:
            swift_type = f"[{list_match.group(1)}]"

        if not swift_type:
            logger.warning(type_info)
            continue

        result.append(
            {"attribute_name": name, "description": prose, "swift_type": swift_type}
        )

    return result


def enpoint_transform(match):
    path_component = match.group(1)
    name = match.group(2)

    return {"name": name, "path_component": path_component}


def match(line, a_config):
    (matcher, transform) = a_config

    _match = matcher(line)
    if _match:
        return (line, transform(_match))
    else:
        return (line, None)


def matches(configuration, line):
    _matches = [match(line, c) for c in configuration]

    if not (None for (l, t) in _matches if t):
        # logger.warning(line)
        pass

    return (t for (l, t) in _matches)


def writing(xs, fieldnames):
    writer = csv.DictWriter(sys.stdout, fieldnames, delimiter="|")

    writer.writeheader()
    writer.writerows(xs)


def endpoints(lines):
    # e.g. <li><a href="#move-targets">Move Targets</a></li>
    endpoint_pattern = r'\t+<li><a href="#([\w-]+)">([\w ]+)</a></li>'

    patterns = [endpoint_pattern]
    matchers = [partial(re.match, p) for p in patterns]
    transforms = [enpoint_transform]

    configuration = list(zip(matchers, transforms))

    matched = [matches(configuration, line) for line in lines]

    writing(filter(None, chain(*matched)), ["name", "path_component"])


if __name__ == "__main__":
    # reading https://github.com/PokeAPI/pokeapi/blob/master/pokemon_v2/README.md
    lines = sys.stdin.readlines()

    if sys.argv[1] == "Endpoints":
        endpoints(lines)
    # writing(attribute_names(lines), ["attribute_name", "description", "swift_type"])
