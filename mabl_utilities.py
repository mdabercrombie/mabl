#!/usr/bin/env /home/centos/anaconda2/bin/python

from os import makedirs, remove
from os.path import join, isfile, exists, basename
from datetime import date
from shutil import move
import MySQLdb


STATS_DIR = join('/', 'home', 'centos', 'Documents', 'mabl_gamestats')
STATS_DROPBOX = join(STATS_DIR, 'dropbox')
STATS_ARCHIVE = join(STATS_DIR, 'archive')

month_dict = {'Jan': '01',
              'Feb': '02',
              'Mar': '03',
              'Apr': '04',
              'May': '05',
              'June': '06',
              'July': '07',
              'Aug': '08',
              'Sep': '09',
              'Oct': '10',
              'Nov': '11',
              'Dec': '12'}


def convert_team_name_id(nickname):
    """
    Given the team nickname, return the team id from teams table in db.

    :param str nickname: team nickname
    :return str team_id: team id

    :Example:

    >>> convert_team_name_id('Brewers')
    1

    """

    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    nrows = curs.execute("""SELECT * FROM teams
                WHERE team_name = %s""",
                         (nickname,))
    if nrows > 0:
        team_id, location, team_name, team_abbrev = curs.fetchone()
    else:
        # Team not found in db, print error message and return
        print "No team matching {0} found in database."
        return None

    return team_id


def create_stats_filename(subject_line, email_time, ext='.xls'):
    """
    Create a .xls filename from iScore email subject line.

    Returns None if filename already exists.

    :param str subject_line: subject line from iScore email
    :param str email_time: time string representing time in inbox
    :param str ext: file extenstion, expecting .xls or .html for now
    :returns: filename in yyyymmdd_visitors_home_yyyymmddhhMMss format
    :rtype: str

    .. note:: general format of subject line
        'iScore Baseball Game Stats - 1/28/18 Brewers at Dirtbags'

    """
 
    # month_dict = {'Jan': '01',
    #               'Feb': '02',
    #               'Mar': '03',
    #               'Apr': '04',
    #               'May': '05',
    #               'June': '06',
    #               'July': '07',
    #               'Aug': '08',
    #               'Sep': '09',
    #               'Oct': '10',
    #               'Nov': '11',
    #               'Dec': '12'}

    subject_parts = subject_line.split()
    home_team = subject_parts[-1].lower()
    visiting_team = subject_parts[-3].lower()
    game_date = subject_parts[-4].split('/')
    game_date = '20{:02d}{:02d}{:02d}'.format(
        int(game_date[2]), int(game_date[0]), int(game_date[1]))
 
    time_parts = email_time.split()
    time_time = '{0}{1}{2}'.format(time_parts[4].split(':')[0],
                                   time_parts[4].split(':')[1],
                                   time_parts[4].split(':')[2])

    time_stamp = '{:04d}{:02d}{:02d}{:06d}'.format(
        int(time_parts[3]), int(month_dict[time_parts[2]]),
        int(time_parts[1]), int(time_time))

    stats_filename = '{0}_{1}_{2}_{3}{4}'.format(
        game_date, visiting_team, home_team, time_stamp, ext)

    # Check if filename already exists, if so return 'None'
    if isfile(join(STATS_DROPBOX, stats_filename)):
        stats_filename = None

    return stats_filename


def convert_to_mabldb_time(email_time):
    """
    Convert time string from email to 'yyyy-mm-dd' format.

    :param str, datetime email_time: email time
    :returns: date_str
    :rtype: str

    .. note:: email time can be given as a datetime object
        or a couple different expected string formats

    """

    if isinstance(email_time, date):
        # This is a datetime object
        date_str = '{:04d}-{:02d}-{:02d}'.format(
            email_time.year, email_time.month, email_time.day)

    elif email_time.split()[0] in (
            'Sun,', 'Mon,', 'Tue,', 'Wed,', 'Thu,', 'Fri,', 'Sat,'):
        # This is a string from email
        time_parts = email_time.split()
        date_str = '{:04d}-{:02d}-{:02d}'.format(
            int(time_parts[3]), int(month_dict[time_parts[2]]), int(time_parts[1]))

    else:
        # This is a string from email subject line
        time_parts = email_time.split('/')
        date_str = '20{:02d}-{:02d}-{:02d}'.format(
            int(time_parts[2]), int(time_parts[0]), int(time_parts[1]))

    return date_str


def get_teams(email_subject):
    """
    Returns the visiting, home teams from email subject line.

    :param str email_subject: subject line from iScore email
    :returns: visiting_team, home_team
    :rtype: str, str
    """

    subject_parts = email_subject.split()

    return subject_parts[6], subject_parts[8]


def get_game_date(email_subject):
    """Returns the game date in mabldb format."""

    return convert_to_mabldb_time(email_subject.split()[5])


def has_number(input_str):
    """Returns true if input_str contains any numbers."""

    return any(char.isdigit() for char in input_str)


def misspelled_names(first_name, last_name):

    if last_name in 'St.':
        first = 'Kevin'
        last = 'St. Germain'
    elif last_name in ('Beasely', 'Beesely', 'Beaseley'):
        first = 'Austin'
        last = 'Beesley'
    elif first_name in 'Norman' and last_name in 'Campos':
        first = 'Oli'
        last = 'Campos'
    elif last_name in 'Herman':
        first = 'Justin'
        last = 'Herrmann'
    elif last_name in 'MacFarlin':
        first = 'Joseph'
        last = 'McFarlin'
    elif last_name in 'Morris' and first_name in 'Dan':
        first = 'Daniel'
        last = 'Morris'
    elif last_name in 'Hansen' and first_name in 'Joshua':
        first = 'Josh'
        last = 'Hansen'
    elif last_name in 'Hirouji':
        first = 'Darren'
        last = 'Hiroji'
    elif last_name in 'Kaahanui':
        first = 'Peter'
        last = "Ka'ahanui"
    else:
        first = str(first_name)
        last = str(last_name)

    return first, last


def convert_inp(float_inp):
    """
    Convert inp from decimal value (0.000, 0.333, 0.667, etc) to (0.0, 0.1, 0.2) for cleaner display.

    :param float float_inp: inning pitching float value
    :return:
    """

    # Split inp into integer and decimal parts
    i_inp, d_inp = divmod(float_inp, 1)
    d_inp = d_inp*10

    # Look at first digit of decimal part
    # NOTE: repr(3)[0] = 2 and repr(6) = 5, not sure why?
    if int(repr(d_inp)[0]) == 0:
        disp_inp = i_inp + 0.0
    elif int(repr(d_inp)[0]) == 3 or int(repr(d_inp)[0]) == 2:
        disp_inp = i_inp + 0.1
    elif int(repr(d_inp)[0]) == 6 or int(repr(d_inp)[0]) == 7 or int(repr(d_inp)[0]) == 5:
        disp_inp = i_inp + 0.2
    else:
        print "{0} innings is not a standard amount!".format(float_inp)
        return None

    return disp_inp


def move_file(filename, origin=STATS_DROPBOX, dest=STATS_ARCHIVE):
    """
    Moves iScore file from dropbox to archive.

    :param str filename: name of file being moved
    :param str origin: path for stats dropbox
    :param str dest: path for stats archive
    :return:
    """

    # Create a yyyymmdd/ directory within archive/ prior to moving
    filename = basename(filename)
    subdir = filename.split('_')[0]
    subdir_path = join(dest, subdir)
    if not exists(subdir_path):
        makedirs(subdir_path)

    try:
        move(join(origin, filename), join(subdir_path, filename))
    except IOError:
        # Check if file is in archive already
        if isfile(join(subdir_path, filename)):
            print "{0} is already in the archive directory".format(filename)
        else:
            print "Unable to move {0} to the archive directory".format(filename)


def del_file(filename, loc=STATS_DROPBOX):
    """
    Deletes given file.

    :param str filename: name of file to be deleted
    :param str loc: directory path where file is located
    :return:
    """

    filename = basename(filename)
    remove(join(filename, loc))


def get_indices(hdr_list):
    """
    Get column indices for iScore .xls stat file.

    :param list hdr_list: list of str header names
    :return:
    """

    # Just worried about pitching for now.
    pitching_indx_list = []
    pitching_indx_list.append(hdr_list.index('Name'))
    pitching_indx_list.append(hdr_list.index('Name'))
    pitching_indx_list.append(hdr_list.index('G'))
    pitching_indx_list.append(hdr_list.index('IP'))
    pitching_indx_list.append(hdr_list.index('W'))
    pitching_indx_list.append(hdr_list.index('L'))
    pitching_indx_list.append(hdr_list.index('SV'))
    pitching_indx_list.append(hdr_list.index('H'))
    pitching_indx_list.append(hdr_list.index('R'))
    pitching_indx_list.append(hdr_list.index('ER'))
    pitching_indx_list.append(hdr_list.index('BB'))
    pitching_indx_list.append(hdr_list.index('K'))
    pitching_indx_list.append(hdr_list.index('HB'))
    pitching_indx_list.append(hdr_list.index('G'))
    pitching_indx_list.append(hdr_list.index('BF'))
    pitching_indx_list.append(hdr_list.index('ERA'))
    pitching_indx_list.append(hdr_list.index('ERA'))
    pitching_indx_list.append(hdr_list.index('BAA'))
    pitching_indx_list.append(hdr_list.index('WHIP'))

    return pitching_indx_list
