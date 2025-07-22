import sys
import requests
import argparse
import json
import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from typing import cast


rarity_key_map = {
    'common': 'C',
    'uncommon': 'U',
    'rare': 'R',
    'mythic': 'M',
}


def fetch_set_from_mtgjson(set_code: str, cache: bool=True):
    set_json_file = f"{set_code}.json"

    json_url_template = f"https://mtgjson.com/api/v5/{set_json_file}"
    json_url = f"https://mtgjson.com/api/v5/{set_json_file}"

    mtg_json = None
    if cache:
        if not os.path.exists(set_json_file):
            # Download the JSON file if it doesn't exist
            r = requests.get(json_url)
            if r.status_code == 200:
                with open(set_json_file, 'w') as f:
                    f.write(r.text)
        if not os.path.exists(set_json_file):
            raise FileNotFoundError(f"JSON file {set_json_file} not found and cache option is enabled.")
        mtg_json = json.load(open(set_json_file, 'r', encoding='utf-8'))
    else:
        r = requests.get(json_url)
        if r.status_code == 200:
            mtg_json = json.loads(r.text)

    if mtg_json is None:
        raise ValueError(f"Failed to retrieve or parse JSON data from {json_url}")

    # Some set validation
    assert mtg_json['data']['code'] == setcode, f"Set code mismatch: expected {setcode}, got {mtg_json['data']['code']}"

    card_df = pd.DataFrame(
        mtg_json['data']['cards'],
        columns=[
            "number",
            "name",
            "setCode",
            "artist",
            "rarity",
            "frameEffects",
            "promoType",
            "type",
            "types",
            "isFullArt",
            "isAlternative",
            "isPromo",
            "borderColor"])

    card_df["number"] = card_df["number"].astype(pd.Int32Dtype())
    card_df["name"] = card_df["name"].astype(pd.StringDtype())
    card_df["setCode"] = card_df["setCode"].astype(pd.StringDtype())
    card_df["artist"] = card_df["artist"].astype(pd.StringDtype())
    card_df["rarity"] = card_df["rarity"].astype(pd.StringDtype())

    card_df.sort_values(by='number', inplace=True, ascending=True)

    releaseDate = mtg_json['data']['releaseDate']
    tokenSetCode = mtg_json['data'].get('tokenSetCode', setcode)

    # Capitalize the set type
    settype = mtg_json['data']['type'].capitalize()

    # Handle rarities
    card_df["rarity_code"] = card_df["rarity"].map(rarity_key_map)

    # Correct the rarity codes for basic lands
    card_df.loc[(card_df["rarity_code"] == "C") & card_df["type"].str.contains("Basic Land"), "rarity_code"] = "L"

    return mtg_json, card_df


def fetch_set_from_scryfall(set_code: str,
                            include_extras: bool = True,
                            unique: str = "prints") -> pd.DataFrame:
    """
    Return a pandas DataFrame containing **all** cards for the
    given Scryfall set code.

    Parameters
    ----------
    set_code        : 3-letter or 5-letter set code (e.g. 'eoe', 'spg')
    include_extras  : include_variants / promos / tokens if True
    unique          : 'prints' (every printing) or 'cards' (1 per name)

    Returns
    -------
    pd.DataFrame    : one row per card object (see https://scryfall.com/docs/api/cards)
    """
    base_url = "https://api.scryfall.com/cards/search"
    # Scryfall’s search syntax; include:extras pulls in showcase, tokens, etc.
    query = f"set:{set_code}"
    if include_extras:
        query += " include:extras"

    params = {"q": query, "order": "set", "unique": unique, "page": 1}
    data = []

    with tqdm(desc=f"Fetching {set_code.upper()} pages") as pbar:
        while True:
            resp = requests.get(base_url, params=params, timeout=30)
            resp.raise_for_status()            # throw if HTTP error
            payload = resp.json()
            data.extend(payload["data"])

            if not payload.get("has_more"):
                break

            # follow the paging cursor
            next_url = payload["next_page"]
            # next_page already includes q/order/unique, so wipe params
            params = {}
            base_url = next_url
            pbar.update(1)

    # Make a DataFrame; keep every field or slice later
    df = pd.DataFrame(data)

    # Some post-processing
    df['collector_number'] = df['collector_number'].astype(pd.Int32Dtype())
    assert df['collector_number'].isna().sum() == 0
    df.set_index('collector_number', inplace=True)
    df['rarity_code'] = df['rarity'].map(rarity_key_map)

    return df


bonus_header = """\
[metadata]
Code={setcode}
Date={releaseDate}
Name={name}
Type={settype}
ScryfallCode={setcode}
"""

expansion_header = """\
[metadata]
Code={setcode}
Date={releaseDate}
Name={name}
Type={settype}
ScryfallCode={setcode}
TokensCode={tokenSetCode}
# TODO: Fill booster definitions
BoosterSlots=
Booster=
Prerelease=
BoosterBox=
"""

# Token section
def token_section(token_df, file=sys.stdout):
    for v, row in token_df.iterrows():
        color = row['colors']
        if type(color) is list:
            if len(color) == 0:
                color = 'c'
            elif len(color) == 1:
                color = color[0].lower()
            else:
                color = None
        elif pd.isna(row['colors']):
            color = 'c'
        else:
            raise ValueError(f"Unexpected color value: {color}")

        def pt_correct(pt):
            return pt.replace('*', 'x')

        power = row['power']
        toughness = row['toughness']
        if pd.isna(power) or pd.isna(toughness):
            pt_section = None
        else:
            pt_section = f"{pt_correct(power)}_{pt_correct(toughness)}"
        name = row['name'].replace(' ','_')
        if color is not None:
            name_elements = [color]
            if pt_section is not None:
                name_elements.append(pt_section)
            name_elements.append(name.lower())
            if len(row['keywords']) > 0:
                name_elements.append('_'.join(row['keywords']).lower())
            name = '_'.join(name_elements)

            print(f"{v} {name} @{row['artist']}", file=file)
        else:
            print(f"{v} {name.lower()} @{row['artist']}", file=file)

if __name__ == '__main__':
    from mk_ic import install    
    install()

    parser = argparse.ArgumentParser(description='Edition File Generator')
    _ = parser.add_argument('-c', action='store', dest='setcode', help='Required setcode', required=True)
    _ = parser.add_argument('-n', action='store', dest='name', help='Name of edition', required=True)
    _ = parser.add_argument('-t', action='store', dest='settype', help='Type of edition (Expansion, Duel_Decks, Other, etc)', default='Expansion')
    _ = parser.add_argument('--cache', action='store_true', help="Use the local cached version if available")
    _ = parser.add_argument('--mode', default='main', help="Script mode")

    args = parser.parse_args()

    setcode = cast(str, args.setcode)
    name = cast(str, args.name)
    settype = cast(str, args.settype)
    mode = cast(str, args.mode)

    types = [ 'Expansion', 'Collector_Edition' ]
    if settype not in types:
        raise ValueError(f"Invalid type '{settype}'. Valid modes are: {types}")

    if settype == 'Collector_Edition':
        # Fetch data from Scryfall
        cards_df = fetch_set_from_scryfall(setcode, include_extras=True, unique="prints")

        release_date = cards_df['released_at'].iloc[0]

        with open(f"{setcode}.txt", 'w') as f:
            _ = f.write(bonus_header.format_map({
                'setcode': setcode,
                'releaseDate': release_date,
                'name': name,
                'settype': settype
            }))

            _ = f.write("\n[cards]\n")
            for n, row in cards_df.iterrows():
                _ = f.write(f"{n} {row['rarity_code']} {row['name']} @{row['artist']}\n")
    elif settype == 'Expansion':
        # Fetch data from Scryfall
        cards_df = fetch_set_from_scryfall(setcode, include_extras=True, unique="prints")
        release_date = cards_df['released_at'].iloc[0]

        # Fetch set data from MTGJSON
        mtgjson, mtgjson_cards_df = fetch_set_from_mtgjson(setcode, cache=args.cache)

        # Write the token section
        token_setcode = mtgjson['data']['tokenSetCode']
        token_df = fetch_set_from_scryfall(token_setcode, include_extras=True, unique="prints")

        with open(f"{setcode}.txt", 'w') as f:
            _ = f.write(expansion_header.format_map({
                'setcode': setcode,
                'releaseDate': release_date,
                'name': name,
                'settype': settype,
                'tokenSetCode': mtgjson
            }))
            _ = f.write("\n[cards]\n")

            _ = f.write("\n[tokens]\n")
            token_section(token_df, file=f)

        sys.exit(0)

        card_df = scryfall_df[scryfall_df['type_line'].str.contains("Basic Land")]
        with pd.option_context('display.max_rows', None):
            ic(card_df.iloc[0,:])

        card_df['collector_number'] = card_df['collector_number'].astype(pd.Int32Dtype())
        card_df.set_index('collector_number', inplace=True, drop=False)
        card_df.sort_index(inplace=True)
        ic(card_df['collector_number'].describe())
        ic(card_df.head(n=20))

        edition_file = f"{setcode}.txt"
        with open(edition_file, 'w', encoding='utf-8') as f:

            _ = f.write("\n")
            _ = f.write('[cards]\n')
            for _, row in card_df.iterrows():
                _ = f.write(f"{row['number']} {rarity_key_map[row['rarity']]} {row['name']} @{row['artist']}\n")

        # Load token data
        #ic(cards[0])
        #ic(cards[250])

        #ic(card_df.head(n=20))
        ic(card_df[card_df['name'] == "Forest"])
