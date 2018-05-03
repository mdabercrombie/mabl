#!/usr/bin/env /home/centos/anaconda2/bin/python

import MySQLdb
from argparse import ArgumentParser


class Game:
    """
    Common base class for all games.
    """

    def __init__(self, season_id=None, game_date=None, game_time=None, week=None, game_number=None, field=None, 
                 home_team_id=None, visiting_team_id=None, home_final=None, visitors_final=None, home_hits=None, 
                 visitors_hits=None, home_runs=None, visitors_runs=None, game_type='regular', winning_team_id=None,
                 msg=None, photos_link=None, video_link=None, stats='n', home_visitors_known='y'):
        self.season_id = season_id
        self.game_date = game_date
        self.game_time = game_time
        self.week = week
        self.game_number = game_number
        self.field = field
        self.home_team_id = home_team_id
        self.visiting_team_id = visiting_team_id
        self.home_final = home_final
        self.visitors_final = visitors_final
        self.home_hits = home_hits
        self.visitors_hits = visitors_hits
        self.home_runs = home_runs
        self.visitors_runs = visitors_runs
        self.game_type = game_type
        self.winning_team_id = winning_team_id
        self.msg = msg
        self.photos_link = photos_link
        self.video_link = video_link
        self.stats = stats
        self.home_visitors_known = home_visitors_known


def get_player_name(player_id):

    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    curs.execute("""SELECT first_name, last_name FROM players WHERE player_id = %s""", (player_id,))
    name = curs.fetchone()

    player_name = "{0} {1}".format(name[0], name[1])

    return player_name


def batting_by_season(season_id, games_played, game_type):

    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    # Get maximum player_id for this season_id
    curs.execute("""SELECT batting.player_id FROM batting
        INNER JOIN games ON batting.game_id = games.id
        WHERE games.season_id = %s ORDER BY batting.player_id DESC
        LIMIT 1""", (season_id,))
    max_player_id, = curs.fetchone()

    for player_id in range(max_player_id+1):
        if game_type == 'Regular':
            ngames = curs.execute("""SELECT pa, ab, r, h, 2b, 3b, hr, bb, 
                         rbi, k, sb, cs, sac, hbp, tb FROM batting
                         INNER JOIN games ON batting.game_id = games.id
                         WHERE batting.player_id = %s AND games.season_id = %s
                         AND games.game_type = 'Regular'""",
                                  (player_id, season_id))
        elif game_type == 'Playoffs':
            ngames = curs.execute("""SELECT pa, ab, r, h, 2b, 3b, hr, bb, 
                         rbi, k, sb, cs, sac, hbp, tb FROM batting
                         INNER JOIN games ON batting.game_id = games.id
                         WHERE batting.player_id = %s AND games.season_id = %s
                         AND games.game_type 
                         IN ('Playoffs Round 1', 'Playoffs Round 2', 'Championship Series')""",
                                  (player_id, season_id))
        elif game_type == 'Combined':
            ngames = curs.execute("""SELECT pa, ab, r, h, 2b, 3b, hr, bb, 
                         rbi, k, sb, cs, sac, hbp, tb FROM batting
                         INNER JOIN games ON batting.game_id = games.id
                         WHERE batting.player_id = %s AND games.season_id = %s""",
                                  (player_id, season_id))            
        if ngames > 0:
            pa_list = []
            ab_list = []
            r_list = []
            h_list = []
            double_list = []
            triple_list = []
            hr_list = []
            bb_list = []
            rbi_list = []
            k_list = []
            sb_list = []
            cs_list = []
            sac_list = []
            hbp_list = []
            tb_list = []

            games = curs.fetchall()
            for game in games:
                pa_list.append(game[0])
                ab_list.append(game[1])
                r_list.append(game[2])
                h_list.append(game[3])
                double_list.append(game[4])
                triple_list.append(game[5])
                hr_list.append(game[6])
                bb_list.append(game[7])
                rbi_list.append(game[8])
                k_list.append(game[9])
                sb_list.append(game[10])
                cs_list.append(game[11])
                sac_list.append(game[12])
                hbp_list.append(game[13])
                tb_list.append(game[14])

            # Sum over each list and insert results
            pa_total = sum(pa_list)
            ab_total = sum(ab_list)
            r_total = sum(r_list)
            h_total = sum(h_list)
            double_total = sum(double_list)
            triple_total = sum(triple_list)
            hr_total = sum(hr_list)
            bb_total = sum(bb_list)
            rbi_total = sum(rbi_list)
            k_total = sum(k_list)
            sb_total = sum(sb_list)
            cs_total = sum(cs_list)
            sac_total = sum(sac_list)
            hbp_total = sum(hbp_list)
            tb_total = sum(tb_list)

            if ab_total > 0:
                avg = round(float(h_total)/float(ab_total), 3)
                slg = round(float(tb_total)/float(ab_total), 3)
            else:
                avg = -100
                slg = -100
            if pa_total > 0:
                obp = round(float(h_total+bb_total+hbp_total)/float(pa_total), 3)
                ops = obp+slg
            else:
                obp = -100
                ops = -100

            # Get team_id from rosters table
            nrows = curs.execute("""SELECT team_id FROM rosters
                        WHERE season_id = %s AND player_id = %s""", (season_id, player_id))
            if nrows > 0:
                team_id, = curs.fetchone()
            else:
                team_id = 0

            # Determine if this player qualifies for average-based leaders, at least 2.5 pa per team game
            # Get season length from seasons table
            curs.execute("""SELECT season_length FROM seasons
                WHERE id = %s""", (season_id,))
            season_length, = curs.fetchone()

            qualify = 'n'
            if pa_total >= season_length*2.5:
                qualify = 'y'
            elif season_id == 19:
                if pa_total >= 2.5*games_played:
                    qualify = 'y'

            write_to_db = 1
            if write_to_db:
                # Figure out if there is an entry for this player_id and season_id in 'batting_by_season'
                # If there is, update it, if there isn't create it
                curs.execute("""SELECT COUNT(*) FROM batting_by_season
                    WHERE season_id = %s AND player_id = %s AND game_type = %s""", (season_id, player_id, game_type))

                db_entry, = curs.fetchone()
                if db_entry:
                    curs.execute("""UPDATE batting_by_season
                        SET team_id = %s, games = %s, pa = %s, ab = %s, r = %s, h = %s, 2b = %s, 3b = %s, hr = %s, 
                        bb = %s, rbi = %s, k = %s, sb = %s, cs = %s, sac = %s, hbp = %s, tb = %s, avg = %s, obp = %s,
                        slg = %s, ops = %s, qualify = %s
                        WHERE season_id = %s AND player_id = %s AND game_type = %s""",
                                 (team_id, ngames, pa_total, ab_total, r_total, h_total, double_total, triple_total,
                                  hr_total, bb_total, rbi_total, k_total, sb_total, cs_total, sac_total, hbp_total,
                                  tb_total, avg, obp, slg, ops, qualify, season_id, player_id, game_type))
                    print "UPDATED batting_by_season for player_id {0}".format(player_id)
                else:
                    curs.execute("""INSERT INTO batting_by_season
                        (season_id, player_id, team_id, games, pa, ab, r, h, 2b, 3b, hr, bb, rbi, k, sb, cs, sac, hbp,
                        tb, avg, obp, slg, ops, qualify, game_type) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s)""",
                                 (season_id, player_id, team_id, ngames, pa_total, ab_total, r_total, h_total,
                                  double_total, triple_total, hr_total, bb_total, rbi_total, k_total, sb_total,
                                  cs_total, sac_total, hbp_total, tb_total, avg, obp, slg, ops, qualify, game_type))
                    print "INSERTED batting_by_season for player_id {0}".format(player_id)



def pitching_by_season(season_id, games_played, game_type):

    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    # Get maximum player_id for this season_id
    curs.execute("""SELECT pitching.player_id FROM pitching
        INNER JOIN games ON pitching.game_id = games.id
        WHERE games.season_id = %s ORDER BY pitching.player_id DESC
        LIMIT 1""", (season_id,))
    max_player_id, = curs.fetchone()

    for player_id in range(max_player_id+1):
        if game_type == 'Regular':
            ngames = curs.execute("""SELECT inp, w, l, sv, h, r, er, k, 
                         bb, hbp, gs, cg, ab FROM pitching
                         INNER JOIN games ON pitching.game_id = games.id
                         WHERE pitching.player_id = %s AND games.season_id = %s
                         AND games.game_type = 'Regular'""",
                                  (player_id, season_id))
        elif game_type == 'Playoffs':
            ngames = curs.execute("""SELECT inp, w, l, sv, h, r, er, k, 
                         bb, hbp, gs, cg, ab FROM pitching
                         INNER JOIN games ON pitching.game_id = games.id
                         WHERE pitching.player_id = %s AND games.season_id = %s
                         AND games.game_type
                         IN ('Playoffs Round 1', 'Playoffs Round 2', 'Championship Series')""",
                                  (player_id, season_id))
        elif game_type == 'Combined':
            ngames = curs.execute("""SELECT inp, w, l, sv, h, r, er, k, 
                         bb, hbp, gs, cg, ab FROM pitching
                         INNER JOIN games ON pitching.game_id = games.id
                         WHERE pitching.player_id = %s AND games.season_id = %s""",
                                  (player_id, season_id))
        if ngames > 0:
            inp_list = []
            w_list = []
            l_list = []
            sv_list = []
            h_list = []
            r_list = []
            er_list = []
            k_list = []
            bb_list = []
            hbp_list = []
            gs_list = []
            cg_list = []
            ab_list = []

            games = curs.fetchall()
            for game in games:
                inp_list.append(game[0])
                w_list.append(game[1])
                l_list.append(game[2])
                sv_list.append(game[3])
                h_list.append(game[4])
                r_list.append(game[5])
                er_list.append(game[6])
                k_list.append(game[7])
                bb_list.append(game[8])
                hbp_list.append(game[9])
                gs_list.append(game[10])
                cg_list.append(game[11])
                ab_list.append(game[12])

            # Sum over each list and insert results
            inp_total = sum(inp_list)
            w_total = sum(w_list)
            l_total = sum(l_list)
            sv_total = sum(sv_list)
            h_total = sum(h_list)
            r_total = sum(r_list)
            er_total = sum(er_list)
            k_total = sum(k_list)
            bb_total = sum(bb_list)
            hbp_total = sum(hbp_list)
            gs_total = sum(gs_list)
            cg_total = sum(cg_list)
            ab_total = sum(ab_list)

            # Fix potential issues with inp_total
            partial_inp = round(inp_total % 1, 1)
            full_inp = round(inp_total, 0)
            if partial_inp > 0.2:
                (add_inp, part_inp) = divmod(partial_inp, 0.3)
                inp_total = full_inp + add_inp + part_inp

            # Get float inp value for stat calculations involving inp
            if round(inp_total % 1, 1) == 0.1:
                inp_float = round(inp_total) + 0.333333
            elif round(inp_total % 1, 1) == 0.2:
                inp_float = round(inp_total) + 0.666667
            else:
                inp_float = inp_total

            if inp_total > 0:
                bb_inp = round(float(bb_total)/float(inp_float), 2)
                k_inp = round(float(k_total)/float(inp_float), 2)
                era = round((float(er_total)/float(inp_total))*9.00, 2)
                oba = round(float(h_total)/(float(inp_total)*3+float(h_total)), 3)
                whip = round(float(h_total+bb_total)/float(inp_float), 2)
            else:
                bb_inp = -100
                k_inp = -100
                era = -100
                oba = -100
                whip = -100

            # Get team_id from rosters table
            nrows = curs.execute("""SELECT team_id FROM rosters
                        WHERE season_id = %s AND player_id = %s""", (season_id, player_id))
            if nrows > 0:
                team_id, = curs.fetchone()
            else:
                team_id = 0

            # Determine if this player qualifies for average-based leaders, at least 2 inp per team game
            # Get season length from seasons table
            curs.execute("""SELECT season_length FROM seasons
                WHERE id = %s""", (season_id,))
            season_length, = curs.fetchone()

            qualify = 'n'
            if inp_total >= season_length*2:
                qualify = 'y'
            elif season_id == 19:
                if inp_total >= 2*games_played:
                    qualify = 'y'

            write_to_db = 1
            if write_to_db:
                # Figure out if there is an entry for this player_id and season_id in 'batting_by_season'
                # If there is, update it, if there isn't create it
                curs.execute("""SELECT COUNT(*) FROM pitching_by_season
                    WHERE season_id = %s AND player_id = %s AND game_type = %s""", (season_id, player_id, game_type))

                db_entry, = curs.fetchone()
                if db_entry:
                    curs.execute("""UPDATE pitching_by_season
                        SET team_id = %s, games = %s, inp = %s, w = %s, l = %s, sv = %s, h = %s, r = %s, er = %s, 
                        k = %s, bb = %s, hbp = %s, gs = %s, cg = %s, ab = %s, era = %s, oba = %s, whip = %s, 
                        bb_inp = %s, k_inp = %s, qualify = %s
                        WHERE season_id = %s AND player_id = %s AND game_type = %s""",
                                 (team_id, ngames, inp_total, w_total, l_total, sv_total, h_total, r_total, er_total,
                                  k_total, bb_total, hbp_total, gs_total, cg_total, ab_total, era, oba, whip,
                                  bb_inp, k_inp, qualify, season_id, player_id, game_type))
                    print "UPDATED pitching_by_season for player_id {0}".format(player_id)
                else:
                    curs.execute("""INSERT INTO pitching_by_season
                        (season_id, player_id, team_id, games, inp, w, l, sv, h, r, er, k, bb, hbp, gs, cg, ab, era, 
                        oba, whip, bb_inp, k_inp, qualify, game_type) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s)""",
                                 (season_id, player_id, team_id, ngames, inp_total, w_total, l_total, sv_total, h_total,
                                  r_total, er_total, k_total, bb_total, hbp_total, gs_total, cg_total, ab_total, era,
                                  oba, whip, bb_inp, k_inp, qualify, game_type))
                    print "INSERTED pitching_by_season for player_id {0}".format(player_id)


def estimate_p_ab(season_id):
    
    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    nrows = curs.execute("""SELECT p.player_id, p.game_id, p.team_id, p.pitching_order, p.inp, p.h, p.ab, p.oba
                    FROM pitching p INNER JOIN games g ON p.game_id = g.id WHERE g.season_id = %s""",
                         (season_id,))

    rows = curs.fetchall()
    for row in rows:
        [player_id, game_id, team_id, pitching_order, inp, h, ab, oba] = row
        if ab > 0:
            continue
        if inp > 0 and oba > 0:
            # Get ab from oba and h
            ab = int(round(float(h)/float(oba)))
        elif oba == 0:
            # Get from inp
            ab = 3*int(str(inp).split('.')[0])+int(str(inp).split('.')[1])
        else:
            # No outs recorded, get ab from h
            ab = int(h)
        curs.execute("""UPDATE pitching SET ab = %s WHERE player_id = %s 
            AND game_id = %s AND team_id = %s AND pitching_order = %s""",
                     (ab, player_id, game_id, team_id, pitching_order))

    print "Completed all {0} rows of season_id {1}".format(nrows, season_id)


def add_team_id():

    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    # Get player_ids
    curs.execute("""SELECT b.season_id, b.player_id, r.team_id FROM batting_by_season b
            INNER JOIN rosters r ON b.player_id = r.player_id
        WHERE b.season_id = r.season_id""")
    rows = curs.fetchall()

    for row in rows:
        season_id, player_id, team_id = row
        curs.execute("""UPDATE batting_by_season SET team_id = %s
            WHERE season_id = %s AND player_id = %s""", (team_id, season_id, player_id))
        print "Set team_id = {0} for season_id = {1} and player_id = {2}".format(team_id, season_id, player_id)

    # Get player_ids
    curs.execute("""SELECT p.season_id, p.player_id, r.team_id FROM pitching_by_season p
            INNER JOIN rosters r ON p.player_id = r.player_id 
        WHERE p.season_id = r.season_id""")
    rows = curs.fetchall()

    for row in rows:
        season_id, player_id, team_id = row
        curs.execute("""UPDATE pitching_by_season SET team_id = %s
            WHERE season_id = %s AND player_id = %s""", (team_id, season_id, player_id))
        print "Set team_id = {0} for season_id = {1} and player_id = {2}".format(team_id, season_id, player_id)


def career_batting():

    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    # Get current season_id
    curs.execute("""SELECT DISTINCT(season_id)
        FROM rosters ORDER BY season_id DESC LIMIT 1""")
    current_season_id, = curs.fetchone()

    # Get maximum player_id
    curs.execute("""SELECT batting.player_id FROM batting
        INNER JOIN games ON batting.game_id = games.id
        ORDER BY batting.player_id DESC
        LIMIT 1""")
    max_player_id, = curs.fetchone()

    for player_id in range(max_player_id+1):

        # Is player active?
        nrows = curs.execute("""SELECT * FROM rosters
                    WHERE player_id = %s AND season_id = %s""",
                             (player_id, current_season_id))
        if nrows > 0:
            active = 'y'
        else:
            active = 'n'

        nseasons = curs.execute("""SELECT DISTINCT(games.season_id)
                       FROM games
                       INNER JOIN batting ON games.id = batting.game_id
                       WHERE batting.player_id = %s""",
                                (player_id,))

        ngames = curs.execute("""SELECT pa, ab, r, h, 2b, 3b, hr, bb, 
                     rbi, k, sb, cs, sac, hbp, tb FROM batting
                     INNER JOIN games ON batting.game_id = games.id
                     WHERE batting.player_id = %s""",
                              (player_id,))
        if ngames > 0:
            pa_list = []
            ab_list = []
            r_list = []
            h_list = []
            double_list = []
            triple_list = []
            hr_list = []
            bb_list = []
            rbi_list = []
            k_list = []
            sb_list = []
            cs_list = []
            sac_list = []
            hbp_list = []
            tb_list = []

            games = curs.fetchall()
            for game in games:
                pa_list.append(game[0])
                ab_list.append(game[1])
                r_list.append(game[2])
                h_list.append(game[3])
                double_list.append(game[4])
                triple_list.append(game[5])
                hr_list.append(game[6])
                bb_list.append(game[7])
                rbi_list.append(game[8])
                k_list.append(game[9])
                sb_list.append(game[10])
                cs_list.append(game[11])
                sac_list.append(game[12])
                hbp_list.append(game[13])
                tb_list.append(game[14])

            # Sum over each list and insert results
            pa_total = sum(pa_list)
            ab_total = sum(ab_list)
            r_total = sum(r_list)
            h_total = sum(h_list)
            double_total = sum(double_list)
            triple_total = sum(triple_list)
            hr_total = sum(hr_list)
            bb_total = sum(bb_list)
            rbi_total = sum(rbi_list)
            k_total = sum(k_list)
            sb_total = sum(sb_list)
            cs_total = sum(cs_list)
            sac_total = sum(sac_list)
            hbp_total = sum(hbp_list)
            tb_total = sum(tb_list)

            if ab_total > 0:
                avg = round(float(h_total)/float(ab_total), 3)
                slg = round(float(tb_total)/float(ab_total), 3)
            else:
                avg = 0.000
                slg = 0.000
            if pa_total > 0:
                obp = round(float(h_total+bb_total+hbp_total)/float(pa_total), 3)
                ops = obp+slg
            else:
                obp = 0.000
                ops = 0.000

            # Get team_id from rosters table
            nrows = curs.execute("""SELECT team_id FROM rosters
                        WHERE player_id = %s ORDER BY season_id DESC""", (player_id,))
            if nrows > 0:
                team_id, = curs.fetchone()
            else:
                team_id = 0

            # Determine if this player qualifies for average-based leaders, at least 250 career pa
            qualify = 'n'
            if pa_total >= 250:
                qualify = 'y'

            write_to_db = 1
            if write_to_db:
                # Figure out if there is an entry for this player_id and season_id in 'career_batting'
                # If there is, update it, if there isn't create it
                curs.execute("""SELECT COUNT(*) FROM career_batting
                    WHERE player_id = %s""", (player_id,))

                db_entry, = curs.fetchone()
                if db_entry:
                    curs.execute("""UPDATE career_batting
                        SET seasons = %s, games = %s, pa = %s, ab = %s, r = %s, h = %s, 2b = %s, 3b = %s, hr = %s, 
                        bb = %s, rbi = %s, k = %s, sb = %s, cs = %s, sac = %s, hbp = %s, tb = %s, avg = %s, obp = %s,
                        slg = %s, ops = %s, qualify = %s, active = %s
                        WHERE player_id = %s""",
                                 (nseasons, ngames, pa_total, ab_total, r_total, h_total, double_total, triple_total,
                                  hr_total, bb_total, rbi_total, k_total, sb_total, cs_total, sac_total, hbp_total,
                                  tb_total, avg, obp, slg, ops, qualify, active, player_id))
                    print "UPDATED career_batting for player_id {0}".format(player_id)
                else:
                    curs.execute("""INSERT INTO career_batting
                        (player_id, seasons, games, pa, ab, r, h, 2b, 3b, hr, bb, rbi, k, sb, cs, sac, hbp, tb, avg, 
                        obp, slg, ops, qualify, active) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s)""",
                                 (player_id, nseasons, ngames, pa_total, ab_total, r_total, h_total, double_total,
                                  triple_total, hr_total, bb_total, rbi_total, k_total, sb_total, cs_total, sac_total,
                                  hbp_total, tb_total, avg, obp, slg, ops, qualify, active))
                    print "INSERTED career_batting for player_id {0}".format(player_id)


def career_pitching():

    # Open database connection
    db = MySQLdb.connect(host="localhost", user="stats",
                         passwd="stats", db="baseball_stats")
    curs = db.cursor()

    # Get current season_id
    curs.execute("""SELECT DISTINCT(season_id)
        FROM rosters ORDER BY season_id DESC LIMIT 1""")
    current_season_id, = curs.fetchone()

    # Get maximum player_id for this season_id
    curs.execute("""SELECT pitching.player_id FROM pitching
        INNER JOIN games ON pitching.game_id = games.id
        ORDER BY pitching.player_id DESC LIMIT 1""")
    max_player_id, = curs.fetchone()

    for player_id in range(max_player_id+1):

        # Is player active?
        nrows = curs.execute("""SELECT * FROM rosters
                    WHERE player_id = %s AND season_id = %s""",
                             (player_id, current_season_id))
        if nrows > 0:
            active = 'y'
        else:
            active = 'n'

        nseasons = curs.execute("""SELECT DISTINCT(games.season_id)
                       FROM games
                       INNER JOIN pitching ON games.id = pitching.game_id
                       WHERE pitching.player_id = %s""", (player_id,))

        ngames = curs.execute("""SELECT inp, w, l, sv, h, r, er, k, 
                     bb, hbp, gs, cg, ab FROM pitching
                     INNER JOIN games ON pitching.game_id = games.id
                     WHERE pitching.player_id = %s""", (player_id,))

        if ngames > 0:
            inp_list = []
            w_list = []
            l_list = []
            sv_list = []
            h_list = []
            r_list = []
            er_list = []
            k_list = []
            bb_list = []
            hbp_list = []
            gs_list = []
            cg_list = []
            ab_list = []

            games = curs.fetchall()
            for game in games:
                inp_list.append(game[0])
                w_list.append(game[1])
                l_list.append(game[2])
                sv_list.append(game[3])
                h_list.append(game[4])
                r_list.append(game[5])
                er_list.append(game[6])
                k_list.append(game[7])
                bb_list.append(game[8])
                hbp_list.append(game[9])
                gs_list.append(game[10])
                cg_list.append(game[11])
                ab_list.append(game[12])

            # Sum over each list and insert results
            inp_total = sum(inp_list)
            w_total = sum(w_list)
            l_total = sum(l_list)
            sv_total = sum(sv_list)
            h_total = sum(h_list)
            r_total = sum(r_list)
            er_total = sum(er_list)
            k_total = sum(k_list)
            bb_total = sum(bb_list)
            hbp_total = sum(hbp_list)
            gs_total = sum(gs_list)
            cg_total = sum(cg_list)
            ab_total = sum(ab_list)

            # Fix potential issues with inp_total
            partial_inp = round(inp_total % 1, 1)
            full_inp = round(inp_total, 0)
            if partial_inp > 0.2:
                (add_inp, part_inp) = divmod(partial_inp, 0.3)
                inp_total = full_inp + add_inp + part_inp

            # Get float inp value for stat calculations involving inp
            if round(inp_total % 1, 1) == 0.1:
                inp_float = round(inp_total) + 0.333333
            elif round(inp_total % 1, 1) == 0.2:
                inp_float = round(inp_total) + 0.666667
            else:
                inp_float = inp_total

            if inp_total > 0:
                bb_inp = round(float(bb_total)/float(inp_float), 2)
                k_inp = round(float(k_total)/float(inp_float), 2)
                era = round((float(er_total)/float(inp_total))*9.00, 2)
                oba = round(float(h_total)/(float(inp_total)*3+float(h_total)), 3)
                whip = round(float(h_total+bb_total)/float(inp_float), 2)
            else:
                bb_inp = -100
                k_inp = -100
                era = -100
                oba = -100
                whip = -100

            # Determine if this player qualifies for average-based leaders, at least 200 career inp
            qualify = 'n'
            if inp_total >= 200:
                qualify = 'y'

            write_to_db = 1
            if write_to_db:
                # Figure out if there is an entry for this player_id and season_id in 'batting_by_season'
                # If there is, update it, if there isn't create it
                curs.execute("""SELECT COUNT(*) FROM career_pitching
                    WHERE player_id = %s""", (player_id,))

                db_entry, = curs.fetchone()
                if db_entry:
                    curs.execute("""UPDATE career_pitching
                        SET seasons = %s, games = %s, inp = %s, w = %s, l = %s, sv = %s, h = %s, r = %s, er = %s, 
                        k = %s, bb = %s, hbp = %s, gs = %s, cg = %s, ab = %s, era = %s, oba = %s, whip = %s, 
                        bb_inp = %s, k_inp = %s, qualify = %s, active = %s
                        WHERE player_id = %s""",
                                 (nseasons, ngames, inp_total, w_total, l_total, sv_total, h_total, r_total, er_total,
                                  k_total, bb_total, hbp_total, gs_total, cg_total, ab_total, era, oba, whip,
                                  bb_inp, k_inp, qualify, active, player_id))
                    print "UPDATED career_pitching for player_id {0}".format(player_id)
                else:
                    curs.execute("""INSERT INTO career_pitching
                        (player_id, seasons, games, inp, w, l, sv, h, r, er, k, bb, hbp, gs, cg, ab, era, oba, whip, 
                        bb_inp, k_inp, qualify, active) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s)""",
                                 (player_id, nseasons, ngames, inp_total, w_total, l_total, sv_total, h_total, r_total,
                                  er_total, k_total, bb_total, hbp_total, gs_total, cg_total, ab_total, era, oba, whip,
                                  bb_inp, k_inp, qualify, active))
                    print "INSERTED career_pitching for player_id {0}".format(player_id)


#games_played = 6
# Valid types are: 'Regular', 'Playoffs', 'Combined'
#for game_type in ('Regular', 'Combined'):
#    for season_id in range(19, 0, -1):
#        batting_by_season(season_id, games_played, game_type)
#        pitching_by_season(season_id, games_played, game_type)

#career_batting()
#career_pitching()


def main():

    parser = ArgumentParser()
    parser.add_argument("games", help="how many games have been played this season", type=int)
    parser.add_argument("--season_id", default=19, help="season id of season to update", type=int)

    results = parser.parse_args()
    games_played = results.games
    season_id = results.season_id

    # Valid types are: 'Regular', 'Playoffs', 'Combined'
    for game_type in ('Regular', 'Combined'):
        batting_by_season(season_id, games_played, game_type)
        pitching_by_season(season_id, games_played, game_type)

        # for season_id in range(19, 0, -1):
        #     batting_by_season(season_id, games_played, game_type)
        #     pitching_by_season(season_id, games_played, game_type)

    career_batting()
    career_pitching()


if __name__ == "__main__":
    main()
