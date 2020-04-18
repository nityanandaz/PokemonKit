echo "Will Generate $1"
cat ../pokeapi/pokemon_v2/README.md |\
python3 parse.py $1|\
gyb ./Templates/$1.swift.gyb > ./Sources/PokemonKit/$1.swift
