#!/usr/bin/env /home/centos/anaconda2/bin/python

from os import listdir
from os.path import join
import xlrd
import MySQLdb
from collections import namedtuple
from mabl_utilities import convert_team_name_id, misspelled_names, \
    convert_inp, get_indices, has_number, move_file, del_file, get_player_name

STATS_DIR = join('/', 'home', 'centos', 'Documents', 'mabl_gamestats')
STATS_DROPBOX = join(STATS_DIR, 'dropbox')
STATS_ARCHIVE = join(STATS_DIR, 'archive')


def set_stats_flag(game_id):
    """
    Set games.stats = 'y'.

    :param int game_id: id of game entry
    :return:
    """

    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    curs.execute("""UPDATE games SET stats = 'y' WHERE id = %s""",
                 (game_id,))


def check_w_l(game_id):
    """
    Check that a win and loss have been assigned for this game. Ask user for input
    and update the database accordingly if decisions have not been entered.

    :param int game_id: id of game entry
    :return:
    """

    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    # Getting winning_team_id and losing_team_id
    curs.execute("""SELECT home_team_id, visiting_team_id, winning_team_id
        FROM games WHERE id = %s""", (game_id,))

    game_results = curs.fetchall()
    home_team_id, visiting_team_id, winning_team_id = game_results[0]

    if winning_team_id == home_team_id:
        losing_team_id = visiting_team_id
    elif winning_team_id == visiting_team_id:
        losing_team_id = home_team_id
    else:
        # winning_team_id doesn't match either of the expected teams
        print "No match found for winning_team_id!"
        return

    # Check if a win and loss has been assigned to pitchers
    w = curs.execute("""SELECT player_id FROM pitching 
            WHERE w = 1 AND game_id = %s""", (game_id,))

    if w == 0:
        # If no winner pitcher has been assigned, list players who pitched for the
        # winning team and ask user to assign the win.
        nrows = curs.execute("""SELECT p.pitching_order, plr.first_name, plr.last_name,
                    p.player_id, t.team_name, p.inp, p.h, p.r, p.er, p.k, p.bb
                    FROM pitching p 
                    INNER JOIN players plr 
                        ON p.player_id = plr.player_id
                    INNER JOIN teams t
                        ON p.team_id = t.id
                    WHERE p.game_id = %s AND p.team_id = %s""",
                             (game_id, winning_team_id))

        win_pitch_id = None
        if nrows == 1:
            # If only one pitcher for winning team, they get win
            row = curs.fetchall()
            win_pitch_id = row[0][3]

        elif nrows > 1:
            # If multiple pitchers for winning team, decide who gets win
            rows = curs.fetchall()

            print "{0: <3} {1: <20} {2: <10} {3: <12} {4: <5} {5: <4}" \
                      " {6: <4} {7: <4} {8: <4} {9: <4}".format(
                '', 'Player Name', 'Player ID', 'Team', 'INP', 'H', 'R',
                'ER', 'K', 'BB')
            for row in rows:
                pitching_order = row[0]
                player_name = "{0} {1}".format(row[1], row[2])
                player_id = row[3]
                team_name = row[4]
                inp = row[5]
                h = row[6]
                r = row[7]
                er = row[8]
                k = row[9]
                bb = row[10]
                print "{0: <3} {1: <20} {2: <10} {3: <12} {4: <5} {5: <4}" \
                      " {6: <4} {7: <4} {8: <4} {9: <4}".format(
                    pitching_order, player_name, player_id, team_name,
                    inp, h, r, er, k, bb)

        if not win_pitch_id:
            # Ask user to input player_id of pitcher who should get the win
            win_pitch_id = raw_input("No win assigned, enter player_id of winning "
                                     "pitcher [or just press Enter to skip]: ")

        # Update the database
        curs.execute("""UPDATE pitching SET w = 1 WHERE game_id = %s
            AND player_id = %s""", (game_id, win_pitch_id))

        # Get the name of the pitcher who was assigned the win and print to screen
        print "Win assigned to {0}.\n".format(get_player_name(win_pitch_id))
    else:
        print "Win assigned to {0}.\n".format(get_player_name(curs.fetchone()[0]))

    l = curs.execute("""SELECT player_id FROM pitching
            WHERE l = 1 AND game_id = %s""", (game_id,))

    if l == 0:
        # If no losing pitcher has been assigned, list players who pitched for the
        # losing team and ask user to assign the loss.
        nrows = curs.execute("""SELECT p.pitching_order, plr.first_name, plr.last_name,
                    p.player_id, t.team_name, p.inp, p.h, p.r, p.er, p.k, p.bb
                    FROM pitching p 
                    INNER JOIN players plr 
                        ON p.player_id = plr.player_id
                    INNER JOIN teams t
                        ON p.team_id = t.id
                    WHERE p.game_id = %s AND p.team_id = %s""",
                             (game_id, losing_team_id))

        loss_pitch_id = None
        if nrows == 1:
            # If only one pitcher for losing team, they get win
            row = curs.fetchall()
            loss_pitch_id = row[0][3]

        elif nrows > 1:
            # If multiple pitchers for winning team, decide who gets win
            rows = curs.fetchall()

            print "{0: <3} {1: <20} {2: <10} {3: <12} {4: <5} {5: <4}" \
                      " {6: <4} {7: <4} {8: <4} {9: <4}".format(
                '', 'Player Name', 'Player ID', 'Team', 'INP', 'H', 'R',
                'ER', 'K', 'BB')
            for row in rows:
                pitching_order = row[0]
                player_name = "{0} {1}".format(row[1], row[2])
                player_id = row[3]
                team_name = row[4]
                inp = row[5]
                h = row[6]
                r = row[7]
                er = row[8]
                k = row[9]
                bb = row[10]
                print "{0: <3} {1: <20} {2: <10} {3: <12} {4: <5} {5: <4}" \
                      " {6: <4} {7: <4} {8: <4} {9: <4}".format(
                    pitching_order, player_name, player_id, team_name,
                    inp, h, r, er, k, bb)

        if not loss_pitch_id:
            loss_pitch_id = raw_input("No loss assigned, enter player_id of losing "
                                      "pitcher [or just press Enter to skip]: ")

        # Update the database
        curs.execute("""UPDATE pitching SET l = 1 WHERE game_id = %s
            AND player_id = %s""", (game_id, loss_pitch_id))

        # Get the name of the pitcher who was assigned the win and print to screen
        print "Loss assigned to {0}.\n".format(get_player_name(loss_pitch_id))
    else:
        print "Loss assigned to {0}.\n".format(get_player_name(curs.fetchone()[0]))


def update_db(game, overwrite_flag=True):
    # Open mysql connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    # Check if season has been entered into the db, if not, create it
    # season_id = get_season_id(season_info)

    # Get team_ids
    team_ids = [convert_team_name_id(game.visiting_team),
                convert_team_name_id(game.home_team)]

    # Get game_id
    nrows = curs.execute("""SELECT id FROM games WHERE game_date = %s
                AND home_team_id = %s AND visiting_team_id = %s""",
                         (game.game_date, team_ids[1], team_ids[0]))
    if nrows == 0:
        print "No matching games between {0} and {1} on {2} found " \
              "in the database".format(game.visiting_team, game.home_team, game.game_date)

        return
    elif nrows == 1:
        game_id, = curs.fetchone()
    else:
        print "Multiple games returned between {0} and {1} on {2}, " \
              "skipping for now".format(game.visiting_team, game.home_team, game.game_date)
        return

    # Check if the games field entries have already been entered for this game
    curs.execute("""SELECT home_final, visitors_final, home_hits, visitors_hits,
        home_errors, visitors_errors FROM games WHERE id = %s""", (game_id,))
    row, = curs.fetchall()
    if None not in row and not overwrite_flag:
        print "Entry for game between {0} and {1} on {2} already found, " \
            "skipping database update.".format(
                game.visiting_team, game.home_team, game.game_date)
        print
        return None, None

    curs.execute("""UPDATE games 
        SET home_final = %s, visitors_final = %s, home_hits = %s,
        visitors_hits = %s, home_errors = %s, visitors_errors = %s,
        home_runs = %s, visitors_runs = %s, winning_team_id = %s
        WHERE id = %s""",
                 (game.home_total, game.visitors_total, game.home_hits, game.visitors_hits,
                  game.home_errors, game.visitors_errors, str(game.home_runs),
                  str(game.visitors_runs), convert_team_name_id(game.winning_team),
                  game_id))

    print "Updated entry for game {0} between {1} and {2} on {3}" \
        .format(game_id, game.visiting_team, game.home_team, game.game_date)

    return game_id, team_ids


def update_db_batting(game_id, team_ids, visitors_batting, home_batting, overwrite_flag=True):
    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    # First check for and remove any existing entries for this game
    nrows = curs.execute("""SELECT * FROM batting
                WHERE game_id = %s""", (game_id,))
    if nrows > 0:
        if overwrite_flag:
            print "Existing batting entries for game {0} will be overwritten.".format(game_id)
            curs.execute("""DELETE FROM batting
                WHERE game_id = %s""", (game_id,))
        else:
            print "Existing pitching entries for game {0} found, skipping.".format(game_id)
            print
            return False

    # Insert batting stats
    for team_indx, batting_stats in enumerate([visitors_batting, home_batting]):

        # Loop over each player in visitors_batting
        # [first_name, last_name, order, AB, R, H, 2B, 
        #  3B, HR, RBI, BB, SO, HBP, SB, CS, SacB, SacF, AVG, OBP, SLG]

        # Get batting.player_id from first_name, last_name
        for lineup_spot, player in enumerate(batting_stats):
            # First check for and remove any underscores
            last_name = str(player[1])
            if '_' in last_name:
                last_name = last_name.split('_')[0]

            # Check for known aliases
            first_name, last_name = misspelled_names(str(player[0]), last_name)

            nrows = curs.execute("""SELECT player_id FROM players
                        WHERE first_name = %s AND last_name = %s""",
                                 (first_name, last_name))
            if nrows > 0:
                player_id = curs.fetchone()
            else:
                # Need to add this player to the database, check with user first
                add_player = raw_input(
                    "{0} {1} not found in database, add player? (y/n) ".format(first_name, last_name))
                if add_player == 'y':
                    curs.execute("""INSERT INTO players (first_name, last_name)
                        VALUES (%s, %s)""", (first_name, last_name))
                    curs.execute("""SELECT LAST_INSERT_ID()""")
                    player_id = curs.fetchone()
                else:
                    # If user entered 'n', ask them for the correct player_id
                    use_player_id = raw_input("Enter the desired player_id: ")
                    player_id = int(use_player_id)

            # Use player_id to update batting
            pa = int(player[3]) + int(player[10]) + int(player[12]) + int(player[15]) + int(player[16])
            try:
                ops = float(player[18]) + float(player[19])
            except:
                ops = None

            # Get total bases
            tb = player[5] + player[6] + 2 * player[7] + 3 * player[8]

            # Get sacrifices
            sac = player[15] + player[16]

            curs.execute("""INSERT INTO batting (player_id, game_id, team_id, batting_order,
                pa, ab, r, h, 2b, 3b, hr, bb, rbi, k, sb, cs, sac, hbp, tb, avg, obp, slg, ops)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s)""", (player_id, game_id, team_ids[team_indx], player[2],
                                             pa, player[3], player[4], player[5],
                                             player[6], player[7], player[8],
                                             player[10], player[9], player[11], player[13],
                                             player[14], sac, player[12], tb,
                                             player[17], player[18], player[19], ops))

    return True


def update_db_pitching(game_id, team_ids, visitors_pitching, home_pitching, overwrite_flag=True):
    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    # First check for and remove any existing entries for this game
    nrows = curs.execute("""SELECT * FROM pitching
                WHERE game_id = %s""", (game_id,))
    if nrows > 0:
        if overwrite_flag:
            print "Existing pitching entries for game {0} will be overwritten.".format(game_id)
            print
            curs.execute("""DELETE FROM pitching
                WHERE game_id = %s""", (game_id,))
        else:
            print "Existing pitching entries for game {0} found, skipping.".format(game_id)
            print
            return False

    # Insert pitching stats
    for team_indx, pitching_stats in enumerate([visitors_pitching, home_pitching]):

        # Insert visiting team's pitching stats
        for player_indx, player in enumerate(pitching_stats):
            # First check for and remove any underscores
            last_name = str(player[1])
            if '_' in last_name:
                last_name = last_name.split('_')[0]

            # Check for known aliases
            first_name, last_name = misspelled_names(str(player[0]), last_name)

            nrows = curs.execute("""SELECT player_id FROM players
                        WHERE first_name = %s AND last_name = %s""",
                                 (first_name, last_name))

            if nrows > 0:
                player_id = curs.fetchone()
            else:
                # Need to add this player to the database, check with user first
                add_player = raw_input(
                    "{0} {1} not found in database, add player? (y/n) ".format(first_name, last_name))
                if add_player == y:
                    curs.execute("""INSERT INTO players (first_name, last_name)
                        VALUES (%s, %s)""", (first_name, last_name))
                    curs.execute("""SELECT LAST_INSERT_ID()""")
                    player_id = curs.fetchone()
                else:
                    # If user entered 'n', ask them for the correct player_id
                    use_player_id = raw_input("Enter the desired player_id: ")
                    player_id = int(use_player_id)

            # inp = player[3], w = player[4], l = player[5], sv = player[6], h = player[7],
            # r = player[8], er = player[9], bb= player[10], k = player[11], hbp = player[12],
            # cg = player[13], ab = player[14], era = player[15], oba = player[17], whip = player[18] 

            # Check that we're not dividing by 0.0 inp
            if player[3] > 0:
                bb_inp = round(player[10] / player[3], 2)
                k_inp = round(player[11] / player[3], 2)
                era = round((player[9] / player[3]) * 9.00, 2)
            else:
                bb_inp = -100
                k_inp = -100
                era = -100
                player[17] = -100
                player[18] = -100

            if player_indx == 0:
                gs = 1
            else:
                gs = 0

            inp = convert_inp(float(player[3]))

            curs.execute("""INSERT INTO pitching (player_id, game_id, team_id, pitching_order, 
                inp, w, l, sv, h, r, er, bb, hbp, k, gs, cg, ab, era, oba, whip, bb_inp, k_inp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s)""", (player_id, game_id, team_ids[team_indx], int(player[2]),
                                     float(inp), int(player[4]), int(player[5]),
                                     int(player[6]), int(player[7]), int(player[8]),
                                     int(player[9]), int(player[10]), int(player[12]),
                                     int(player[11]), gs, int(player[13]), int(player[14]), era,
                                     float(player[17]), round(float(player[18]), 2), bb_inp, k_inp))

    # Check that W-L was awarded for this game, if not provide user dialog
    check_w_l(game_id)

    db.close()
    return True


def read_iscore_xls(xls_file, game_id, team_ids):
    """Opens and reads excel file from iScore."""

    wb = xlrd.open_workbook(xls_file)

    visitors_batting = []
    visitors_pitching = []
    home_batting = []
    home_pitching = []

    for sheet_name in wb.sheet_names():

        if sheet_name == 'VisitorBatting':
            xl_sheet = wb.sheet_by_name(sheet_name)

            # Cycle through and get all the visitors batting stats
            visitors_batting = []
            batting_indx = 4
            # Check if visitors name column is not blank
            # If not, get all necessary fields, enter this list into visitors_batting
            while xl_sheet.cell(batting_indx, 1).value != 'TOTALS':
                player_line = []
                # Get all stats for a player 'player_line', put these in 'visitors_batting'
                for stat_col in [1, 1, 2, 4, 5, 6, 9, 10, 11, 12, 14, 17, 18, 19, 20, 21, 22, 13, 25, 27]:
                    player_line.append(xl_sheet.cell(batting_indx, stat_col).value)
                visitors_batting.append(player_line)

                # Adjust for players name
                visitors_batting[batting_indx - 4][0] = visitors_batting[batting_indx - 4][0].split(' ')[0]
                visitors_batting[batting_indx - 4][1] = visitors_batting[batting_indx - 4][1].split(' ')[1]

                # Adjust order
                visitors_batting[batting_indx - 4][2] = batting_indx - 3
                batting_indx += 1

        elif sheet_name == 'VisitorPitching':
            xl_sheet = wb.sheet_by_name(sheet_name)

            # Cycle through and get all the visitors pitching stats
            visitors_pitching = []
            pitching_indx = 4

            # Read column headers to get appropriate indices
            hdr_list = [str(xl_sheet.cell(3, r).value) for r in range(38)]
            pitching_indx_list = get_indices(hdr_list)

            # If not, get all necessary fields, enter this list into visitors_batting
            while xl_sheet.cell(pitching_indx, 1).value != 'TOTALS':
                player_line = []
                # Get all stats for a player 'player_line', put these in 'visitors_batting'
                # for stat_col in [1,1,2,6,3,4,5,19,11,13,20,16,27,2,7,14,14,32,30]:
                for stat_col in pitching_indx_list:
                    player_line.append(xl_sheet.cell(pitching_indx, stat_col).value)
                visitors_pitching.append(player_line)
                # Adjust for players name
                visitors_pitching[pitching_indx - 4][0] = visitors_pitching[pitching_indx - 4][0].split(' ')[0]
                visitors_pitching[pitching_indx - 4][1] = visitors_pitching[pitching_indx - 4][1].split(' ')[1]
                # Adjust order
                visitors_pitching[pitching_indx - 4][2] = pitching_indx - 3
                # Adjust ab (use h and oba)
                try:
                    visitors_pitching[pitching_indx - 4][14] = int(round(
                        visitors_pitching[pitching_indx - 4][7] / visitors_pitching[pitching_indx - 4][17]))
                except:
                    # No hits, just do bf - bb - hbp
                    visitors_pitching[pitching_indx - 4][14] = (
                            visitors_pitching[pitching_indx - 4][14] - visitors_pitching[pitching_indx - 4][10]
                            - visitors_pitching[pitching_indx - 4][12])

                # Adjust cg
                if pitching_indx != 4:
                    visitors_pitching[pitching_indx - 4][13] = 0
                    # Previous pitcher didn't throw a cg either
                    visitors_pitching[pitching_indx - 5][13] = 0

                pitching_indx += 1

        elif sheet_name == 'HomeBatting':
            xl_sheet = wb.sheet_by_name(sheet_name)

            # Cycle through and get all the visitors batting stats
            home_batting = []
            batting_indx = 4
            # Check if visitors name column is not blank
            # If not, get all necessary fields, enter this list into visitors_batting
            while xl_sheet.cell(batting_indx, 1).value != 'TOTALS':
                player_line = []
                # Get all stats for a player 'player_line', put these in 'visitors_batting'
                # for stat_col in range(20):
                for stat_col in [1, 1, 2, 4, 5, 6, 9, 10, 11, 12, 14, 17, 18, 19, 20, 21, 22, 13, 25, 27]:
                    player_line.append(xl_sheet.cell(batting_indx, stat_col).value)
                home_batting.append(player_line)
                # Adjust for players name
                home_batting[batting_indx - 4][0] = home_batting[batting_indx - 4][0].split(' ')[0]
                home_batting[batting_indx - 4][1] = home_batting[batting_indx - 4][1].split(' ')[1]
                # Adjust order
                home_batting[batting_indx - 4][2] = batting_indx - 3
                batting_indx += 1

        elif sheet_name == 'HomePitching':
            xl_sheet = wb.sheet_by_name(sheet_name)

            # Cycle through and get all the visitors pitching stats
            home_pitching = []
            pitching_indx = 4

            # Read column headers to get appropriate indices
            hdr_list = [str(xl_sheet.cell(3, r).value) for r in range(38)]
            pitching_indx_list = get_indices(hdr_list)

            # If not, get all necessary fields, enter this list into visitors_batting
            while xl_sheet.cell(pitching_indx, 1).value != 'TOTALS':
                player_line = []
                # Get all stats for a player 'player_line', put these in 'visitors_batting'
                # for stat_col in [1,1,2,6,3,4,5,19,11,13,20,16,27,2,7,14,14,32,30]:
                for stat_col in pitching_indx_list:
                    player_line.append(xl_sheet.cell(pitching_indx, stat_col).value)
                home_pitching.append(player_line)
                # Adjust for players name
                home_pitching[pitching_indx - 4][0] = home_pitching[pitching_indx - 4][0].split(' ')[0]
                home_pitching[pitching_indx - 4][1] = home_pitching[pitching_indx - 4][1].split(' ')[1]
                # Adjust order
                home_pitching[pitching_indx - 4][2] = pitching_indx - 3
                # Adjust ab (use h and oba)
                try:
                    home_pitching[pitching_indx - 4][14] = int(round(
                        home_pitching[pitching_indx - 4][7] / home_pitching[pitching_indx - 4][17]))

                except:
                    # No hits, just do bf - bb - hbp
                    home_pitching[pitching_indx - 4][14] = (
                            home_pitching[pitching_indx - 4][14] - home_pitching[pitching_indx - 4][10]
                            - home_pitching[pitching_indx - 4][12])

                # Adjust cg
                if pitching_indx != 4:
                    home_pitching[pitching_indx - 4][13] = 0
                    # Previous pitcher didn't throw a cg either
                    home_pitching[pitching_indx - 5][13] = 0

                pitching_indx += 1

        else:
            continue

    update_batting_flag = update_db_batting(game_id, team_ids, visitors_batting, home_batting)
    update_pitching_flag = update_db_pitching(game_id, team_ids, visitors_pitching, home_pitching)

    set_stats_flag(game_id)
    return update_batting_flag, update_pitching_flag


def get_stats():
    # 1) Check dropbox for new files, move to archive dir
    # 2) Find all files for a given game; choose best one
    # 3) Update games, batting, pitching tables

    for stats_file in listdir(STATS_DROPBOX):
        game_id = None
        team_ids = None
        if stats_file.endswith(".html"):

            # Get teams and game date from file name
            # Convert game date from yyyymmdd to yyyy-mm-dd
            # Capitalize team names
            game_date = stats_file.split('_')[0]
            game_date = '{0}-{1}-{2}'.format(
                game_date[0:4], game_date[4:6], game_date[6:8])
            visiting_team = stats_file.split('_')[1].title()
            home_team = stats_file.split('_')[2].title()

            # Open html file and extract info
            with open(join(STATS_DROPBOX, stats_file), 'r') as f:
                html_lines = f.readlines()
                for line_num, html_line in enumerate(html_lines):

                    if "Team" in html_line:
                        header_line = html_line.split('TH>')[2:]
                        visitors_line = html_lines[line_num + 1].split("class='dataCell'>")[1:]
                        home_line = html_lines[line_num + 2].split("class='dataCell'>")[1:]

                        new_line = []
                        for col in header_line:
                            entry = col.split('<')[0]
                            if len(entry) > 0:
                                new_line.append(col.split('<')[0])
                        header_line = new_line

                        new_line = []
                        for col in visitors_line:
                            if has_number(col):
                                new_line.append(col.split('<')[0])
                        visitors_line = new_line

                        new_line = []
                        for col in home_line:
                            if has_number(col):
                                new_line.append(col.split('<')[0])
                        home_line = new_line

                        # Get runs by inning, total runs, hits, errors, and winning team
                        visitors_runs = []
                        home_runs = []
                        for indx, inn in enumerate(header_line):
                            # Cycle over header line until reaching 'R'
                            if has_number(inn):
                                visitors_runs.append(int(visitors_line[indx]))
                                try:
                                    home_runs.append(int(home_line[indx]))
                                except:
                                    # Home team didn't bat in the bottom of the last inn
                                    home_runs = '{0}, -]'.format(
                                        str(home_runs).split(']')[0])

                                    # Get runs
                            elif inn == 'R':
                                visitors_total = int(visitors_line[indx])
                                home_total = int(home_line[indx])

                            # Get hits
                            elif inn == 'H':
                                visitors_hits = int(visitors_line[indx])
                                home_hits = int(home_line[indx])

                            # Get errors
                            elif inn == 'E':
                                visitors_errors = int(visitors_line[indx])
                                home_errors = int(home_line[indx])

                        # Figure out which team won
                        if int(visitors_total) > int(home_total):
                            winning_team = visiting_team
                        elif int(home_total) > int(visitors_total):
                            winning_team = home_team
                        else:
                            winning_team = None

                        print_flag = True
                        if print_flag:
                            print "game date:       {0}".format(game_date)
                            print "visitors:        {0}".format(visiting_team)
                            print "home:            {0}".format(home_team)
                            print "visitors runs:   {0}".format(visitors_runs)
                            print "home runs:       {0}".format(home_runs)
                            print "visitors total:  {0}".format(visitors_total)
                            print "home total:      {0}".format(home_total)
                            print "visitors hits:   {0}".format(visitors_hits)
                            print "home hits:       {0}".format(home_hits)
                            print "visitors errors: {0}".format(visitors_errors)
                            print "home errors:     {0}".format(home_errors)
                            print

                        game = namedtuple('game', ['game_date', 'visiting_team', 'home_team',
                                                   'visitors_runs', 'home_runs',
                                                   'visitors_total', 'home_total',
                                                   'visitors_hits', 'home_hits',
                                                   'visitors_errors', 'home_errors',
                                                   'winning_team'])
                        new_game = game(game_date, visiting_team, home_team, visitors_runs,
                                        home_runs, visitors_total, home_total, visitors_hits,
                                        home_hits, visitors_errors, home_errors, winning_team)

                        # Update the database
                        db_flag = True
                        if db_flag:
                            game_id, team_ids = update_db(new_game)

                            # Move .html file to archive directory
                            move_file(stats_file)
                        break

        # Now open .xls file for this game and import batting and pitching stats
        xls_file = '{0}.xls'.format(stats_file.split('.')[0])
        if game_id is not None and team_ids is not None:
            xls_file = join(STATS_DROPBOX, xls_file)

            update_flags = read_iscore_xls(xls_file, game_id, team_ids)

            # Move .xls file to archive directory if it was written to db, otherwise delete
            if update_flags[0] and update_flags[1]:
                move_file(xls_file)
            else:
                del_file(xls_file)


def main():

    get_stats()


if __name__ == "__main__":
    main()
