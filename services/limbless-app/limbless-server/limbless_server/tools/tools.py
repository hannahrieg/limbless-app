from typing import Optional, Union, TypeVar
import difflib

import pandas as pd

from .. import logger

tab_10_colors = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf"
]


def check_indices(df: pd.DataFrame) -> pd.DataFrame:
    indices_present = []

    for idx in ["index_1", "index_2", "index_3", "index_4"]:
        if idx not in df.columns:
            df[idx] = None
    
    if "index_1" in df.columns and not df["index_1"].isna().all():
        indices_present.append("index_1")

    if "index_2" in df.columns and not df["index_2"].isna().all():
        indices_present.append("index_2")

    if "index_3" in df.columns and not df["index_3"].isna().all():
        indices_present.append("index_3")

    if "index_4" in df.columns and not df["index_4"].isna().all():
        indices_present.append("index_4")
    
    duplicate_barcode_combinations = (df[indices_present + ["lane"]].duplicated(keep=False))
    
    df["index_warning"] = None
    df["index_error"] = None

    for idx, row in df.iterrows():
        if row["index_1"] == row["index_2"]:
            df.at[idx, "index_warning"] = "Index 1 and 2 are the same for the sample."
        if row["index_1"] == row["index_3"]:
            df.at[idx, "index_warning"] = "Index 1 and 3 are the same for the sample."
        if row["index_1"] == row["index_4"]:
            df.at[idx, "index_warning"] = "Index 1 and 4 are the same for the sample."
        if row["index_2"] == row["index_3"] and row["index_2"] is not None:
            df.at[idx, "index_warning"] = "Index 2 and 3 are the same for the sample."
        if row["index_2"] == row["index_4"] and row["index_2"] is not None:
            df.at[idx, "index_warning"] = "Index 2 and 4 are the same for the sample."
        if row["index_3"] == row["index_4"] and row["index_3"] is not None:
            df.at[idx, "index_warning"] = "Index 3 and 4 are the same for the sample."
        if row[indices_present].isna().all():
            df.at[idx, "index_error"] = "No indices are present for the sample."
        if duplicate_barcode_combinations[idx]:
            df.at[idx, "index_error"] = "Duplicate barcode combination for two or more samples in lane."

    return df


def titlecase_with_acronyms(val: str) -> str:
    return " ".join([c[0].upper() + c[1:] for c in val.split(" ")])


def make_filenameable(val, keep: list[str] = ['-', '.', '_']) -> str:
    return "".join(c for c in str(val) if c.isalnum() or c in keep)


def make_alpha_numeric(val, keep: list[str] = [".", "-", "_"], replace_white_spaces_with: Optional[str] = "_") -> Optional[str]:
    if pd.isna(val) or val is None or val == "":
        return None
    
    if replace_white_spaces_with is not None:
        val = val.strip().replace(" ", replace_white_spaces_with)
    return "".join(c for c in val if c.isalnum() or c in keep)
    

def parse_float(val: Union[int, float, str, None]) -> Optional[float]:
    if isinstance(val, int) or isinstance(val, float):
        return float(val)
    if isinstance(val, str):
        try:
            return float("".join(c for c in val if c.isnumeric() or c == "." or c == "-"))
        except ValueError:
            return None
    return None


def parse_int(val: Union[int, str, None]) -> Optional[int]:
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        try:
            return int("".join(c for c in val if c.isnumeric() or c == "-"))
        except ValueError:
            return None
    return None


T = TypeVar('T')


def mapstr(
    word: str, tuples: list[tuple[str, T]], cutoff: float = 0.5,
    cap_sensitive: bool = False, filter_non_alphanumeric: bool = True,
) -> T | None:
    
    if pd.isna(word):
        return None

    if not cap_sensitive:
        tuples = [(k.lower(), v) for k, v in tuples]

    if filter_non_alphanumeric:
        tuples = [("".join(c for c in k if c.isalnum()), v) for k, v in tuples]

    tuples = [(k.replace(" ", "").replace("_", "").replace("-", ""), v) for k, v in tuples]

    tt = dict(tuples)

    matches = difflib.get_close_matches(word, tt.keys(), n=1, cutoff=cutoff)
    if (match := next(iter(matches), None)) is None:
        return None

    return tt[match]


def connect_similar_strings(
    refs: list[tuple[str, str]], data: list[str],
    similars: Optional[dict[str, str | int]] = None, cutoff: float = 0.5
) -> dict:
    search_dict = dict([(val.lower().replace(" ", "").replace("_", "").replace("-", ""), key) for key, val in refs])

    res = []
    for word in data:
        _word = word.lower().replace(" ", "").replace("_", "").replace("-", "")
        if similars is not None and _word in similars.keys():
            res.append((similars[_word], 1.0))
        else:
            closest_match = difflib.get_close_matches(word, search_dict.keys(), n=1, cutoff=cutoff)
            if len(closest_match) == 0:
                res.append(None)
            else:
                score = difflib.SequenceMatcher(None, word, closest_match[0]).ratio()
                res.append((search_dict[closest_match[0]], score))

    data = dict(zip(data, res))
    bests = {}
    for key, val in data.items():
        if val is None:
            continue
        
        if val[0] in bests.keys():
            if val[1] > bests[val[0]][1]:
                bests[val[0]] = (key, val[1])
        else:
            bests[val[0]] = (key, val[1])

    res = {}
    for key, val in data.items():
        if val is None:
            res[key] = None
            continue

        if val[0] in bests.keys():
            if bests[val[0]][0] == key:
                res[key] = val[0]
            else:
                res[key] = None
    return res
