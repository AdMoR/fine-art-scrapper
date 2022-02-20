import re
import itertools


def parse_to_text_tokens(presentation):
    return list(
        map(lambda x: x.strip(" …"),
            filter(lambda x: len(set(x)) > 1,
                   presentation.split("\n"))
            ))


def identify_lot_infos(lot_tokens):
    mandatory_infos_func = [identify_lot_id, identify_author, identify_materials]
    mandatory_tokens = list()
    for fn in mandatory_infos_func:
        rez = list(filter(None, map(fn, lot_tokens)))
        if len(rez) == 0:
            return []
        else:
            mandatory_tokens.extend(rez)

    funcs = [identify_date, identify_size, identify_volume, identify_fake,
             identify_authenticity, identify_defect]
    identified_tokens = list(
        filter(None, map(lambda x: x[0](x[1]), itertools.product(funcs, lot_tokens)))
    )
    return mandatory_tokens + identified_tokens


def identify_estimation_and_price(filtered_str):
    filtered_str = filtered_str.replace("\xa0", "")
    match = re.search(
        "Résultat\s+:\s+(?P<result>\w+)\s+(?P<currency_opt>\w*)\s+/\s+Estimation\s+:\s+(?P<estimation_low>[0-9]+)\s+-\s+(?P<estimation_high>[0-9]+)\s+(?P<currency>[A-Z]*)",
        filtered_str)
    if match:
        return match.groupdict()


def str_reverse(str_):
    return "".join(reversed(str_))


def identify_author(filtered_str):
    """
    Pattern 1, 2 : match "Jean-Sébastien D'ASNIERE POUET (1901-1965)", Irène PAGES (1934)
    Pattern Ecol : Ecole truc du 18ème
    Pattern Ecole 2 : Ecole truc vers 1890
    Pattern 5 : match "D'après Frank RIBERA"
    Pattern 6 : match "D'après RIBERA"
    """
    # Pattern 1 : use reverse to match the largest family name
    match = re.search(
        "\)\s*(?P<death>([0-9]{4})?)\s*\-?\s*(?P<birth>[0-9]{4})\s*\(\s+(?P<surname>[A-Z -']+)\s+(?P<name>([A-Za-z -'éèê]+[A-Z])+)",
        str_reverse(filtered_str))
    # Pattern 1 : use reverse to match the largest family name
    if match:
        return {k: str_reverse(v) for k, v in match.groupdict().items()}
    # Pattern 2 : relaxed from pattern 1
    match = re.search(
        "(?P<name>[A-Za-z -'éèê]+)\s+(?P<surname>[A-Z -']+)\s+\(\s*(?P<birth>[0-9]{4})\s*-\s*(?P<death>([0-9]{4})?)\)",
        filtered_str)
    if match:
        return match.groupdict()
    # Pattern 3 : Ecole something
    match = re.search("(?P<name>Ecole)\s+(?P<surname>\w+)\s*d?u?\s*(?P<birth>1[0-9]{1}\s?ème|2[0-1]{1}\s?ème)",
                      filtered_str)
    if match:
        return match.groupdict()
    # Pattern 4 : Ecole something
    match = re.search("(?P<name>Ecole)\s+(?P<surname>\w+)\s+vers\s+(?P<birth>1[0-9]{3})", filtered_str)
    if match:
        return match.groupdict()
    match = re.search(r"(d?D?'après|D?d?ans le goû?u?t de)\s(?P<name>[A-Za-z -'éèê]+)\s(?P<surname>[A-Z \-']+)", filtered_str)
    if match:
        rez = match.groupdict()
        rez.update({"author": False})
        return rez
    match = re.search(r"(d?D?'après|D?d?ans le goû?u?t de)\s(?P<surname>[A-Z \-']+)", filtered_str)
    if match:
        rez = match.groupdict()
        rez.update({"author": False})
        return rez


def identify_size(filtered_str):
    found = re.search("(?P<width>[0-9]+[,. ]*[0-9]+)\s*\s*(?P<unit_width>[a-z]{0,3})\sx\s*(?P<height>[0-9]+[,. ]*[0-9]*)\s*(?P<unit_height>[a-z]{0,3})", filtered_str)
    if found:
        return {k: v.strip(" ") for k, v in found.groupdict().items()}


def identify_volume(filtered_str):
    """
    TODO : 17.5 x 11.5 cm
    18 x 25, 5 cm
    H : 74 - L: 96 - P: 58 cm
    """
    match = re.search(
        "H\s?:\s?(?P<height>[0-9]+)\W*L\s?:\s?(?P<width>[0-9]+)\W*P\s?:\s?(?P<depth>[0-9]+)\s?(?P<unit>[a-z]{0,3})",
        filtered_str)
    if match:
        return match.groupdict()


def identify_date(filtered_str):
    """
    Todo : Daté 83, Daté en 1634
    """
    for match_format in ["(1[0-9]{3})", "(20[0-2]{1}[0-9]{1})"]:
        date_format_one = re.search(match_format, filtered_str)
        if date_format_one is not None:
            return int(date_format_one[1])
    for match_format in ["(1[0-9]{1})\s?ème", "(2[0-1]{1})\s?ème"]:
        date_format_one = re.search(match_format, filtered_str)
        if date_format_one is not None:
            return (int(date_format_one[1]) - 1) * 100 + 50


def identify_lot_id(filtered_str):
    match = re.search("Lot\s+n°\s*(?P<lot_id>[0-9]+)\s*(?P<bis>b?i?s?t?e?r?)", filtered_str)
    if match:
        return match.groupdict()


def identify_fake(filtered_str):
    keyword_list = ["Dans le goût de", "D'après"]
    if any(k.lower() in filtered_str.lower() for k in keyword_list):
        return {"fake": True}


def identify_authenticity(filtered_str):
    """
    TODO: Nous remercions le comité Utrillo pour avoir confirmé l'authenticité de cette toile.
    Nous remercions le comité Utrillo pour avoir confirmé l'authenticité de cette toile.
    """
    keyword_list = ["signé", "signature", "initiales"]
    if any(k.lower() in filtered_str.lower() for k in keyword_list):
        return {"authentic": True}


def identify_materials(str_):
    """
    TODO :
    Huile sur panneau
    Pastel et craie sur papier
    Pastel sur papier
    Pastel signé en bas à droite
    Huile sur toile, Huiles sur toile
    Aquarelle
    Aquarelle sur papier
    Deux aquarelles sur papier
    Deux huiles sur toile
    Huile sur panneau double face
    Gouache sur papier
    dessin et craie sur papier
    Gouache sur carton
    Importante Huile sur panneau, Cadre en bois sculpté et doré
    """
    p = re.compile("(?P<kind>(\w+(\set\s)?)+)\s+sur\s+(?P<material>\w+)")
    match = p.search(str_.lower())
    if match:
        return match.groupdict()
    p = re.compile("(?P<kind>aquarelle|pastel|huile|dessin|craie|gouache)")
    match = p.search(str_.lower())
    if match:
        return match.groupdict()


def identify_defect(str_):
    """
    TODO : (accident) (éclat , brisé en trois…) (accident au cannage)
    (miroir changé) (tranformations) (quelques manques ) (décoloration du vernis, un pied restauré)

    """
    p = re.compile("\((?P<defect>(\D)+)\)")
    match = p.search(str_.lower())
    if match:
        return match.groupdict()
    p = re.compile("(?P<defect>accident|brisé|restauré|manque|éclat|changé)")
    match = p.search(str_.lower())
    if match:
        return match.groupdict()
