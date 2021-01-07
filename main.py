import datetime

import config
import bot


def main():
    date = datetime.date.today().isoformat()
    last_date = datetime.date.today().isoformat()

    args = config.get_args()
    link = 'https://katastar.hr/#/'
    bot.run(args, date, last_date, link)

if __name__ == '__main__':
    main()



