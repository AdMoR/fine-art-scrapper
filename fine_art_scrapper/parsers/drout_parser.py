import itertools
import pickle
import os

import pandas as pd

from fine_art_scrapper.parsers.identification_helpers import identify_lot_id, identify_author, identify_materials, \
    identify_date, identify_size, identify_volume, identify_fake, identify_authenticity, identify_defect, \
    identify_estimation_and_price
from fine_art_scrapper.parsers.cleaning_helpers import handle_missing_line_return


class DroutParser:

    def __init__(self):
        pass

    def parse_checkpoint(self, filepath="./checkpoint_4"):
        all_items = list()
        rez = pickle.load(open(filepath, "rb"))

        for i, sale in enumerate(rez["elements"]):
            if sale is None or sale.catalog_elements is None:
                continue
            for j, element in enumerate(sale.catalog_elements):
                filtered_pres = self.parse_to_text_tokens(element.presentation)
                lot_profile = self.identify_lot_infos(filtered_pres)
                if lot_profile is None:
                    continue
                if element.estimation is not None:
                    price_estim = identify_estimation_and_price(element.estimation.replace("\n", " ").replace("\xa0", ""))
                    if price_estim:
                        lot_profile.update(price_estim)
                lot_profile["presentation"] = ".".join(filtered_pres)
                all_items.append(lot_profile)

        return pd.DataFrame(all_items)

    def identify_lot_infos(self, lot_tokens):
        lot_profile = dict()
        mandatory_infos_func = [identify_lot_id, identify_author, identify_materials]
        mandatory_tokens = list()
        for fn in mandatory_infos_func:
            rez = list(filter(None, map(fn, lot_tokens)))
            if len(rez) == 0:
                print(lot_tokens)
                return None
            else:
                mandatory_tokens.extend(rez)
        list(map(lambda x: lot_profile.update(x), mandatory_tokens))

        funcs = [identify_date, identify_size, identify_volume, identify_fake,
                 identify_authenticity, identify_defect]
        identified_tokens = list(
            filter(None, map(lambda x: x[0](x[1]), itertools.product(funcs, lot_tokens)))
        )
        print(identified_tokens)
        list(map(lambda x: lot_profile.update(x), identified_tokens))
        return lot_profile

    def parse_to_text_tokens(self, presentation):
        presentation = handle_missing_line_return(presentation)
        return list(
            map(lambda x: x.strip(" …"),
                filter(lambda x: len(set(x)) > 1,
                       presentation.split("\n"))
                )
        )


if __name__ == "__main__":
    all_dfs = list()
    save_dir = "./results"
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    parser = DroutParser()
    for path in os.listdir("./my_checkpoints"):
        save_path = os.path.join(save_dir, path + ".csv")
        if not os.path.exists(save_path):
            all_dfs.append(parser.parse_checkpoint(f"./my_checkpoints/{path}"))
            all_dfs[-1].to_csv(save_path)
    final_df = pd.concat(all_dfs)
    final_df.to_csv("final.csv")
