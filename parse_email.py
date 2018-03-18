#!/usr/bin/env /home/centos/anaconda2/bin/python

import imaplib
import email
from argparse import ArgumentParser
from os.path import join
from datetime import date
import mimetypes
from mabl_utilities import convert_to_mabldb_time, create_stats_filename


ORG_EMAIL = '@mauiadultbaseball.com'
FROM_EMAIL = 'stats' + ORG_EMAIL
FROM_PWD = 'hurricanesrock!'
SMTP_SERVER = 'imap.gmail.com'
SMTP_PORT = 993

STATS_DIR = join('/', 'home', 'centos', 'Documents', 'mabl_gamestats')
STATS_DROPBOX = join(STATS_DIR, 'dropbox')
STATS_ARCHIVE = join(STATS_DIR, 'archive')


def readmail(print_flag=True, only_consider_today=True):
    """
    Opens and reads emails to get relevant iScore stats.

    Logs into stats@mauiadultbaseball.com gmail account and searches the
    inbox for iScore emails received that day. A filename is generated
    in the form yyyymmdd_visitors_home_yyyymmddhhmmss (game date then
    time received). The email content is saved as an .html file and the
    gamestats.xls attachment is saved as an .xls file. These are put in
    the mabl_gamestats/dropbox/ directory.

    :param bool print_flag: print basic email information
    :param bool only_consider_today: only read emails from current day
    """

    # Login to gmail with provided credentials
    mail = imaplib.IMAP4_SSL(SMTP_SERVER)
    mail.login(FROM_EMAIL, FROM_PWD)
    
    # Select inbox
    mail.select('inbox')

    # Search emails in inbox
    email_type, data = mail.search(None, 'ALL')
    mail_ids = data[0]
    id_list = mail_ids.split()

    # Get first and last emails to consider
    first_email_id = int(id_list[-10])
    latest_email_id = int(id_list[-1])

    # Loop over each email
    for i in range(latest_email_id, first_email_id, -1):
        typ, data = mail.fetch(i, '(RFC822)')

        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_string(response_part[1])
                email_subject = msg['subject']
                email_from = msg['from']
                email_time = msg['received'].split(';')[1].lstrip()

                # Convert email_time to mabldb format ('yyyy-mm-dd') and check date
                if only_consider_today:
                    if convert_to_mabldb_time(email_time) != convert_to_mabldb_time(date.today()):
                        return

                # If this isn't an iScore email, skip it
                if email_from != 'DoNotReply@iscoresports.com':
                    continue

                # If this is an iScorecast email, skip it
                if email_subject == 'Link to iScorecast':
                    continue

                if print_flag:
                    print 'From :  ' + email_from
                    print 'Subject : ' + email_subject
                    print 'Time : ' + email_time + '\n'

                counter = 1

                if msg.is_multipart():
                    for part in msg.walk():

                        # ctype = part.get_content_type()
                        cdispo = str(part.get('Content-Disposition'))
                        
                        # Find attachments called 'gamestats.xls' and save with new name
                        if 'gamestats.xls' in cdispo:

                            # Create and return filename, 'None' if filename already exists
                            stats_filename = create_stats_filename(email_subject, email_time)

                            if stats_filename is not None:
                                fp = open(join(STATS_DROPBOX, stats_filename), 'wb')
                                fp.write(part.get_payload(decode=True))
                                fp.close()
                            else:
                                continue

                        # Get the html content and save with a new name
                        if part.get_content_maintype() == 'multipart':
                            continue
                        filename = part.get_filename()
                        if not filename:
                            ext = mimetypes.guess_extension(part.get_content_type())
                            if not ext:
                                ext = '.bin'
                            filename = 'part-%03d%s' % (counter, ext)
                        counter += 1

                        if filename == 'part-001.html':
                            # For now, writing html to file and then opening it and reading by line
                            filename = create_stats_filename(email_subject, email_time, '.html')
                            if filename is not None:
                                fp = open(join(STATS_DROPBOX, filename), 'wb')
                                fp.write(part.get_payload(decode=True))
                                fp.close()
                            else:
                                continue

                else:
                    email_body = msg.get_payload(decode=True)
                    print 'Message : ' + email_body + '\n'

    mail.close()
    mail.logout()
 
    # except Exception, e:
    #     print str(e)


def main():

    parser = ArgumentParser()

    parser.add_argument('-p', action='store_true', default=False, help='Print email information')
    parser.add_argument('-t', action='store_true', default=False, help='Only look at emails from today')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    results = parser.parse_args()
    readmail(print_flag=results.p, only_consider_today=results.t)


if __name__ == "__main__":
    main()
