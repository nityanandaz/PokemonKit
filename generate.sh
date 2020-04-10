echo "Generate"
cat ../pokeapi/pokemon_v2/README.md |\
python3 parse.py |\
gyb ./Templates/Types.swift.gyb > ./Sources/PokemonKit/Types.swift
