import argparse
import datetime
import logging
import os
import traceback

import game

def parse_args() -> argparse.Namespace:
    logging_choices = [
        'DEBUG',
        'INFO',
        'WARNING',
        'ERROR',
    ]

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='enable features to aid in debugging')
    parser.add_argument('-l', '--logging', choices=logging_choices, default='WARNING', help='logging level')

    args = parser.parse_args()
    return args

def main() -> None:
    args = parse_args()

    log_dir = 'logs'
    log_filename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log')
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(filename=os.path.join(log_dir, log_filename), filemode='w', level=args.logging)

    try:
        g = game.Game(args.debug)
        g.mainloop()
    except:
        logger = logging.getLogger('main')
        logger.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    main()
