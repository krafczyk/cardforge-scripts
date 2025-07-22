import sys
import requests
import argparse
import json
import os
import re
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

    # Example: choose a skinny set of columns
    # wanted = ["collector_number", "name", "rarity",
    #           "set", "printed_rarity", "border_color",
    #           "promo_types", "frame_effects"]
    # df = df[wanted]

    return df

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


def list_to_tuple(v):
    if type(v) is list:
        return tuple(sorted(v))
    else:
        return v

def natural_key(s: str):
    return [int(tok) if tok.isdigit() else tok
            for tok in re.split(r'(\d+)',s)]

def scryfall_postprocess(df):
    df['collector_number'] = df['collector_number'].astype(pd.StringDtype())
    assert df['collector_number'].isna().sum() == 0
    df_sorted = df.sort_values(
        by='collector_number',
        key=lambda col: col.map(natural_key)
    ).reset_index(drop=True)
    df_sorted.set_index('collector_number', inplace=True)
    df_sorted['rarity_code'] = df_sorted['rarity'].map(rarity_key_map)
    if 'promo_types' in df_sorted.columns:
        df_sorted['promo_types_fixed'] = df_sorted['promo_types'].apply(list_to_tuple)
    if 'frame_effects' in df_sorted.columns:
        df_sorted['frame_effects_fixed'] = df_sorted['frame_effects'].apply(list_to_tuple)
    # Correct rarity of basic lands
    df_sorted.loc[(df_sorted['rarity_code'] == 'C') & df_sorted['type_line'].str.contains('Basic Land'),'rarity_code'] = 'L'
    return df_sorted

def print_cards(df, file=sys.stdout):
    for v, row in df.iterrows():
        file.write(f"{v} {row['rarity_code']} {row['name']} @{row['artist']}\n")
    file.flush()
