import logging.config

from configparser import ConfigParser
from logging import getLogger
from os.path import exists

logger = getLogger(__name__)

config = ConfigParser(interpolation=None)
read_success = not not config.read('radio-bot.cfg')

for section in {'IRC', 'NickServ', 'mpd', 'poll',
                'loggers', 'handlers', 'formatters',
                'logger_root', 'logger_irc', 'logger_config', 'logger_mpd',
                'handler_console',
                'formatter_default'} - set(config.sections()):
    config.add_section(section)

config['IRC'].setdefault('hostname', 'localhost')
config['IRC'].setdefault('port', '6667')
config['IRC'].setdefault('nickname', 'radio-bot')
config['IRC'].setdefault('realname', 'Radio bot')
config['IRC'].setdefault('channel', '#radio')
config['IRC'].setdefault('tls', 'false')
config['IRC'].setdefault('admins', 'op1, op2')

config['NickServ'].setdefault('password', 'secret')
config['NickServ'].setdefault('nickname', '')

config['mpd'].setdefault('hostname', '127.0.0.1')
config['mpd'].setdefault('port', '6600')
config['mpd'].setdefault('timeout', '')

config['poll'].setdefault('poll time', '30')

config['loggers'].setdefault('keys', 'root,config,mpd,irc')
config['handlers'].setdefault('keys', 'console')
config['formatters'].setdefault('keys', 'default')

config['logger_root'].setdefault('level', 'WARNING')
config['logger_root'].setdefault('handlers', 'console')

config['logger_config'].setdefault('level', 'DEBUG')
config['logger_config'].setdefault('handlers', 'console')
config['logger_config'].setdefault('propagate', '0')
config['logger_config'].setdefault('qualname', 'radiobot.config')

config['logger_irc'].setdefault('level', 'DEBUG')
config['logger_irc'].setdefault('handlers', 'console')
config['logger_irc'].setdefault('propagate', '0')
config['logger_irc'].setdefault('qualname', 'radiobot.irc')

config['logger_mpd'].setdefault('level', 'DEBUG')
config['logger_mpd'].setdefault('handlers', 'console')
config['logger_mpd'].setdefault('propagate', '0')
config['logger_mpd'].setdefault('qualname', 'radiobot.mpd')

config['handler_console'].setdefault('class', 'StreamHandler')
config['handler_console'].setdefault('level', 'NOTSET')
config['handler_console'].setdefault('formatter', 'default')
config['handler_console'].setdefault('args', '(sys.stdout,)')

config['formatter_default'].setdefault(
    'format',
    '[%(asctime)s] [%(name)s/%(levelname)s] %(message)s'
)
config['formatter_default'].setdefault('datefmt', '%Y-%m-%d %H:%M:%S')
config['formatter_default'].setdefault('class', 'logging.Formatter')

with open('radio-bot.cfg', 'w') as f:
    config.write(f)

logging.config.fileConfig(config)
logger.info('Config loaded.')

def get_optint(section, option, fallback=None):
    value = config.get(section, option, fallback=None)
    if value is None:
        return fallback
    try:
        value = int(value, 10)
    except ValueError:
        return fallback
    else:
        return value
