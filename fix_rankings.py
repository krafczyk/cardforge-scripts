import argparse
import os
from card_db_interaction import scryfall_postprocess, fetch_set_from_scryfall
from typing import cast

if __name__ == "__main__":
    from mk_ic import install
    install()

    parser = argparse.ArgumentParser(description='Fix draft rankings')
    _ = parser.add_argument("original", type=str, help="Original draft rankings")
    _ = parser.add_argument("main_set", type=str, help="Code for cards to check")
    _ = parser.add_argument("bonus_set", type=str, help="Code for cards to check")
    _ = parser.add_argument("output", type=str, help="output file")
    args = parser.parse_args()

    original_filepath = cast(str, args.original)
    output_filepath = cast(str, args.output)

    if not os.path.exists(original_filepath):
        raise FileNotFoundError(f"Original file '{original_filepath}' does not exist.")

    main_setcode = cast(str, args.main_set)
    bonus_setcode = cast(str, args.bonus_set)

    main_df = scryfall_postprocess(fetch_set_from_scryfall(main_setcode, include_extras=True, unique="prints"))
    bonus_df = scryfall_postprocess(fetch_set_from_scryfall(bonus_setcode, include_extras=True, unique="prints"))
    spg_df = scryfall_postprocess(fetch_set_from_scryfall('SPG', include_extras=True, unique="prints"))

    # Example line of original file content:
    #1|Singularity Rupture|R|EOE

    with open(original_filepath, 'r') as f_i:
        with open(output_filepath, 'w') as f_o:
            for line in f_i:
                # Skip empty lines
                if line.strip() == "":
                    f_o.write(line)
                    continue
                # Skip comments
                if line.startswith("//"):
                    f_o.write(line)
                    continue

                parts = line.strip().split('|')
                name = parts[1]
                setcode = parts[3]

                def df_contains_name(df, name):
                    return df['name'].isin([name]).any()

                # Card must exist in either main or bonus set
                if not df_contains_name(main_df, name) and \
                        not df_contains_name(bonus_df, name) and \
                        not df_contains_name(spg_df, name):
                    print(f"Card '{name}' not found in main, bonus, or SPG set.")
                    f_o.write(line)
                    continue

                if df_contains_name(bonus_df, name):
                    # If the card is in the bonus set, use its bonus set code
                    setcode = bonus_setcode
                    f_o.write(f"{parts[0]}|{name}|{parts[2]}|{setcode}\n")
                    continue

                if df_contains_name(spg_df, name):
                    # If the card is in the bonus set, use its bonus set code
                    setcode = "SPG"
                    f_o.write(f"{parts[0]}|{name}|{parts[2]}|{setcode}\n")
                    continue

                f_o.write(line)


