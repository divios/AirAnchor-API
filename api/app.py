import argparse
import getpass
import logging
import os
import sys
import traceback
import pkg_resources

from colorlog import ColoredFormatter

from api.client import AirAnchorClient


DISTRIBUTION_NAME = 'AirAnchor-api'

DEFAULT_SAWTOOTH = 'http://127.0.0.1:8008'
DEFAULT_RABBITMQ = "http://127.0.0.1:8654"


def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)

    if verbose_level == 0:
        clog.setLevel(logging.WARN)
    elif verbose_level == 1:
        clog.setLevel(logging.INFO)
    else:
        clog.setLevel(logging.DEBUG)

    return clog


def setup_loggers(verbose_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))


def create_parent_parser(prog_name):
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)
    parent_parser.add_argument(
        '-v', '--verbose',
        action='count',
        help='enable more verbose output')
            
    parent_parser.add_argument(
        '--priv-key',
        type=str,
        help='private key path'
    )

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parent_parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='display version information')

    return parent_parser


def create_parser(prog_name):
    parent_parser = create_parent_parser(prog_name)

    parser = argparse.ArgumentParser(
        parents=[parent_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers(title='subcommands', dest='command')

    add_set_parser(subparsers, parent_parser)
    add_show_parser(subparsers, parent_parser)
    add_list_parser(subparsers, parent_parser)

    return parser


def add_set_parser(subparsers, parent_parser):
    message = 'Sends an intkey transaction to set <name> to <value>.'

    parser = subparsers.add_parser(
        'set',
        parents=[parent_parser],
        description=message,
        help='Sends registration petition to store <data> in the blockchain')

    parser.add_argument(
        'data',
        type=str,
        help='data as plain text to register')
    
    parser.add_argument(
        '--rabbitmq',
        type=str,
        default=DEFAULT_RABBITMQ,
        help='specify URL of rabbimq'  
    )


def do_set(args):
    data, rabbitmq_url, key_file = args.data, args.rabbitmq, args.priv_key
    client = _get_client(DEFAULT_SAWTOOTH, rabbitmq_url, key_file)
    result = client.do_location(data)
    print(result)


def add_show_parser(subparsers, parent_parser):
    message = 'Shows the data stored for a specific <key> and <hash>.'

    parser = subparsers.add_parser(
        'show',
        parents=[parent_parser],
        description=message,
        help='Displays the specified data linked to a key and hash')
    
    parser.add_argument(
        'key',
        type=str,
        help='public key of the client that sent the transaction')

    parser.add_argument(
        'hash',
        type=str,
        help='the hash of the transaction')
    
    parser.add_argument(
       '--url',
        type=str,
        default=DEFAULT_SAWTOOTH,
        help='specify URL of REST API')


def do_show(args):
    key, hash, url = args.key, args.hash, args.url
    client = _get_client(url, DEFAULT_RABBITMQ)
    data = client.do_show(key, hash)    
    print('{}: {}'.format(data))


def add_list_parser(subparsers, parent_parser):
    message = 'Shows the values of all keys in intkey state.'

    parser = subparsers.add_parser(
        'list',
        parents=[parent_parser],
        description=message,
        help='Displays all data stored by a client')

    parser.add_argument(
        'key',
        type=str,
        help='public key of the client to look up for')
    
    parser.add_argument(
       '--url',
        type=str,
        default=DEFAULT_SAWTOOTH,
        help='specify URL of REST API')


def do_list(args):
    key, url = args.key, args.url
    client = _get_client(url, DEFAULT_RABBITMQ)
    results = client.do_list(key)
    for pair in results:
        for name, value in pair.items():
            print('{}: {}'.format(name, value))


def _get_client(sawtooth_url, rabbitmq_url, key_path=None):
    return AirAnchorClient(
        sawtooth_rest_url=sawtooth_url,
        rabbitmq_url=rabbitmq_url,
        priv_path=key_path)


def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    if args is None:
        args = sys.argv[1:]
    parser = create_parser(prog_name)
    args = parser.parse_args(args)

    if args.verbose is None:
        verbose_level = 0
    else:
        verbose_level = args.verbose
    setup_loggers(verbose_level=verbose_level)

    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    commands = {
        'set': do_set,
        'show': do_show,
        'list': do_list
    }

    commands[args.command](args)


def main_wrapper():
    # pylint: disable=bare-except
    try:
        main()
    except Exception as err:
        print("Error: {}".format(err), file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    except SystemExit as e:
        raise e
    except:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)