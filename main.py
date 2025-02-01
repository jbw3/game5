import argparse

import game

def parse_args() -> argparse.Namespace:
    logging_choices = [
        'DEBUG',
        'INFO',
        'WARNING',
        'ERROR',
    ]

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--logging', choices=logging_choices, default='WARNING', help='logging level')

    args = parser.parse_args()
    return args

def main() -> None:
    args = parse_args()

    g = game.Game(args.logging)
    g.mainloop()

if __name__ == '__main__':
    main()
