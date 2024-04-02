import argparse
from base import base

from wv import wv
from ky import ky
from pa import pa
from il import il
from oh import oh
from va import va
from al import al


scrapers = {
    # "wv" : wv,
    "ky" : ky,
    "pa" : pa,
    # "il" : il,
    "oh" : oh,
    # "va" : va,
    "al" : al,
}




def main(test=False, reset=False, subset=None, max_age=None):
    if reset:
        base(test=test).reset()
 
    
    for name, scraper in scrapers.items():
        
        if subset and name not in subset:
            continue


        s = scraper(test=test)
        s.update()


    base().export()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--reset", default=False, action='store_true', help="")
    parser.add_argument("--test", default=False, action='store_true', help="")
    parser.add_argument("--subset", default=None, nargs='*', help="")
    parser.add_argument("--max_age", default=None, type=float, help="")
    main(**vars(parser.parse_args()))
