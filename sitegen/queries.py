"""Analytical queries per dataset — each returns plain dicts/lists for the pages."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime
import sqlite3

from .dbutil import rows


# ---------- interventii urs ----------

EVENT_TYPES = ["alungare", "relocare", "impuscare", "eutanasiere", "altele"]
EVENT_TYPE_LABELS = {
    "alungare": "Alungare",
    "relocare": "Relocare",
    "impuscare": "Împușcare",
    "eutanasiere": "Eutanasiere",
    "altele": "Altele",
}


def urs_summary(con: sqlite3.Connection) -> dict:
    total = con.execute("SELECT count(*) FROM interventii_urs").fetchone()[0]
    by_type = dict(con.execute(
        "SELECT event_type, count(*) FROM interventii_urs GROUP BY event_type"
    ).fetchall())
    top_judet = con.execute(
        "SELECT judet, count(*) FROM interventii_urs "
        "WHERE judet != '' GROUP BY judet ORDER BY 2 DESC LIMIT 1"
    ).fetchone()
    ytd = con.execute(
        "SELECT count(*) FROM interventii_urs WHERE data LIKE ?",
        (f"{date.today().year}%",),
    ).fetchone()[0]
    return {
        "total": total,
        "by_type": by_type,
        "top_judet": top_judet[0] if top_judet else None,
        "top_judet_count": top_judet[1] if top_judet else 0,
        "ytd": ytd,
    }


def urs_by_judet(con: sqlite3.Connection, limit: int = 15) -> list[dict]:
    return rows(
        con,
        """SELECT judet, event_type, count(*) AS n
             FROM interventii_urs
             WHERE judet != ''
             GROUP BY judet, event_type""",
    )


def urs_top_judete(con: sqlite3.Connection, limit: int = 10) -> list[str]:
    return [r["judet"] for r in rows(
        con,
        """SELECT judet, count(*) AS n FROM interventii_urs
           WHERE judet != '' GROUP BY judet ORDER BY n DESC LIMIT ?""",
        (limit,),
    )]


def urs_by_month_year(con: sqlite3.Connection) -> dict:
    """Returns {year: [12 monthly counts]} — uses the 'data' column only (sparse but real)."""
    out: dict[str, list[int]] = defaultdict(lambda: [0] * 12)
    for r in rows(
        con,
        "SELECT substr(data,1,4) AS y, substr(data,6,2) AS m, count(*) AS n "
        "FROM interventii_urs WHERE data != '' GROUP BY y, m",
    ):
        try:
            y, m = r["y"], int(r["m"])
            if 1 <= m <= 12:
                out[y][m - 1] = r["n"]
        except Exception:
            continue
    return dict(sorted(out.items()))


def urs_recent(con: sqlite3.Connection, limit: int = 20) -> list[dict]:
    return rows(
        con,
        """SELECT data, judet, uat, event_type, metoda_interventie,
                  descriere_eveniment, sex_urs
             FROM interventii_urs
             WHERE data != ''
             ORDER BY data DESC
             LIMIT ?""",
        (limit,),
    )


def urs_events_with_coords(con: sqlite3.Connection) -> list[dict]:
    return rows(
        con,
        """SELECT event_type, judet, uat, data, lat, long, descriere_eveniment
             FROM interventii_urs
            WHERE lat IS NOT NULL AND lat != ''
              AND long IS NOT NULL AND long != ''
            ORDER BY data DESC""",
    )


# ---------- cmteb ----------

def cmteb_summary(con: sqlite3.Connection) -> dict:
    total = con.execute("SELECT count(*) FROM cmteb").fetchone()[0]
    by_status = dict(con.execute(
        "SELECT status, count(*) FROM cmteb GROUP BY status"
    ).fetchall())
    remediere_active = con.execute(
        "SELECT count(*) FROM cmteb WHERE remediere != ''"
    ).fetchone()[0]
    return {"total": total, "by_status": by_status, "remediere": remediere_active}


def cmteb_nodes(con: sqlite3.Connection) -> list[dict]:
    return rows(
        con,
        "SELECT denumire, Lat, Long, status, stare, culoare, remediere FROM cmteb",
    )


def cmteb_flakiest(con: sqlite3.Connection, limit: int = 10) -> list[dict]:
    """Nodes with most status transitions (distinct _version rows)."""
    return rows(
        con,
        """SELECT c.denumire, count(v._id) AS transitions
             FROM cmteb_version v
             JOIN cmteb c ON c._id = v._item
             GROUP BY v._item
             HAVING transitions > 1
             ORDER BY transitions DESC
             LIMIT ?""",
        (limit,),
    )


# ---------- trafic frontiere ----------

def trafic_snapshot(con: sqlite3.Connection) -> list[dict]:
    return rows(
        con,
        """SELECT Denumire, Timp, Latitude, Longitude, Status, "Tip vehicul" AS vehicul, Sens
             FROM trafic_frontiere_map""",
    )


def trafic_summary(con: sqlite3.Connection) -> dict:
    snap = trafic_snapshot(con)
    waits = []
    for r in snap:
        try:
            waits.append(int(r["Timp"]))
        except Exception:
            pass
    statuses = Counter(r["Status"] for r in snap)
    by_name_max = defaultdict(int)
    for r in snap:
        try:
            by_name_max[r["Denumire"]] = max(by_name_max[r["Denumire"]], int(r["Timp"]))
        except Exception:
            pass
    longest = max(by_name_max.items(), key=lambda x: x[1]) if by_name_max else ("—", 0)
    return {
        "crossings": len({r["Denumire"] for r in snap}),
        "avg_wait": round(sum(waits) / len(waits), 1) if waits else 0,
        "longest_name": longest[0],
        "longest_min": longest[1],
        "statuses": dict(statuses),
    }


def trafic_worst_week(con: sqlite3.Connection, limit: int = 10) -> list[dict]:
    """Crossings with most red+orange hours in the past 7d, via _version."""
    return rows(
        con,
        """SELECT v.Denumire AS name,
                  sum(CASE WHEN v.Status IN ('red','orange') THEN 1 ELSE 0 END) AS bad,
                  count(*) AS total
             FROM trafic_frontiere_version v
             JOIN commits c ON c.id = v._commit
             WHERE c.commit_at >= date('now','-7 day')
             GROUP BY v.Denumire
             ORDER BY bad DESC
             LIMIT ?""",
        (limit,),
    )


# ---------- trafic frontiere — slider snapshots ----------

def _pit_days(con: sqlite3.Connection, version_table: str, days: int) -> list[str]:
    """Return sorted list of the last `days` distinct calendar days for a version table."""
    result = rows(
        con,
        f"""SELECT DISTINCT date(c.commit_at) AS day
              FROM {version_table} v
              JOIN commits c ON c.id = v._commit
              WHERE c.commit_at >= (
                SELECT date(max(c2.commit_at), ?)
                FROM commits c2
                WHERE c2.id IN (SELECT _commit FROM {version_table})
              )
              ORDER BY day""",
        (f"-{days} day",),
    )
    return [r["day"] for r in result]


def _pit_snap(con: sqlite3.Connection, version_table: str, day: str, cols: str) -> list:
    """Point-in-time reconstruction: latest version of each item as of `day`."""
    return rows(
        con,
        f"""SELECT {cols}
              FROM {version_table} v
              JOIN (
                SELECT _item, max(_version) AS mv
                FROM   {version_table}
                WHERE  _commit IN (
                         SELECT id FROM commits
                         WHERE  commit_at < date(?, '+1 day')
                       )
                GROUP BY _item
              ) l ON l._item = v._item AND l.mv = v._version""",
        (day,),
    )


def _bulk_pit(con: sqlite3.Connection, version_table: str, cols: str) -> list:
    """Load all version rows (single query) for in-Python point-in-time reconstruction."""
    return rows(
        con,
        f"""SELECT v._item AS _item, v._version AS _version, date(c.commit_at) AS day, {cols}
              FROM {version_table} v
              JOIN commits c ON c.id = v._commit
              ORDER BY v._item, v._version""",
    )


def _item_histories(all_vers: list) -> dict:
    """Group version rows by _item; return {item_id: (sorted_days, rows_parallel)}."""
    from bisect import insort
    from collections import defaultdict
    by_item: dict = defaultdict(list)
    for r in all_vers:
        by_item[r["_item"]].append(r)
    return by_item


def _lookup(item_rows: list, day: str):
    """Return the latest row for an item as of `day` (rows sorted by _version ascending)."""
    latest = None
    for r in item_rows:
        if r["day"] <= day:
            latest = r
        else:
            break
    return latest


def trafic_map_slider(con: sqlite3.Connection, days: int = 60) -> dict:
    """Pre-baked per-day crossing snapshots.

    Returns {dates, cx, snaps} where:
      cx    = [{n, lat, lng}] indexed list of unique crossing names
      snaps = [[[cx_idx, wait_min, status_int], ...], ...]  — one per date
    status_int: 0=green, 1=orange, 2=red
    Aggregated by Denumire (max wait, worst status) matching the live map.
    """
    selected = _pit_days(con, "trafic_frontiere_map_version", days)
    if not selected:
        return {"dates": [], "cx": [], "snaps": []}

    all_vers = _bulk_pit(
        con, "trafic_frontiere_map_version",
        "v.Denumire AS n, v.Latitude AS lat, v.Longitude AS lng, "
        "CAST(v.Timp AS INTEGER) AS t, v.Status AS s",
    )
    by_item = _item_histories(all_vers)

    STATUS_INT = {"green": 0, "orange": 1, "red": 2}

    # Build crossing index: unique Denumire → (index, lat, lng)
    cx_index: dict[str, int] = {}
    cx_list: list = []
    for vers in by_item.values():
        last = vers[-1]
        name = last["n"] or ""
        if not name or name in cx_index:
            continue
        try:
            lat, lng = round(float(last["lat"]), 4), round(float(last["lng"]), 4)
        except (TypeError, ValueError):
            continue
        cx_index[name] = len(cx_list)
        cx_list.append({"n": name, "lat": lat, "lng": lng})

    snaps = []
    for day in selected:
        # Aggregate by Denumire: max wait, worst status
        agg: dict[str, list] = {}  # name -> [max_wait, max_status_int]
        for vers in by_item.values():
            r = _lookup(vers, day)
            if r is None:
                continue
            name = r["n"] or ""
            if name not in cx_index:
                continue
            t = max(0, int(r["t"] or 0))
            si = STATUS_INT.get(r["s"], 0)
            if name not in agg:
                agg[name] = [t, si]
            else:
                agg[name][0] = max(agg[name][0], t)
                agg[name][1] = max(agg[name][1], si)
        snap = [[cx_index[n], d[0], d[1]] for n, d in agg.items()]
        snaps.append(snap)

    return {"dates": selected, "cx": cx_list, "snaps": snaps}


def cmteb_slider(con: sqlite3.Connection, days: int = 90) -> dict:
    """Pre-baked per-day CMTEB node status snapshots.

    Returns {dates, nodes, snaps} where:
      nodes = [{id, lat, lng, name}] — fixed positions (from current snapshot)
      snaps = [{str(item_id): status_int}] — sparse; missing = 0 (functionale)
    status_int: 0=functionale, 1=deficiente, 2=avarii
    """
    STATUS_INT = {"functionale": 0, "deficiente": 1, "avarii": 2}

    node_rows = rows(con, "SELECT _id, Lat, Long, denumire FROM cmteb")
    nodes = []
    for r in node_rows:
        try:
            lat, lng = round(float(r["Lat"]), 4), round(float(r["Long"]), 4)
        except (TypeError, ValueError):
            continue
        nodes.append({"id": r["_id"], "lat": lat, "lng": lng, "name": r["denumire"] or ""})

    selected = _pit_days(con, "cmteb_version", days)
    if not selected:
        return {"dates": [], "nodes": nodes, "snaps": []}

    all_vers = _bulk_pit(con, "cmteb_version", "v._item AS item_id, v.status AS s")
    by_item = _item_histories(all_vers)

    snaps = []
    for day in selected:
        snap: dict[str, int] = {}
        for item_id, vers in by_item.items():
            r = _lookup(vers, day)
            if r is None:
                continue
            si = STATUS_INT.get(r["s"], 0)
            if si != 0:
                snap[str(item_id)] = si
        snaps.append(snap)

    return {"dates": selected, "nodes": nodes, "snaps": snaps}


def aer_buc_slider(con: sqlite3.Connection, days: int = 60) -> dict:
    """Pre-baked per-day Bucharest air-quality snapshots.

    Returns {dates, stations, snaps} where:
      stations = [{name, lat, lng}]
      snaps = [{station_name: [pm25, pm10]}]
    """
    station_rows = rows(con, "SELECT name, lat, long FROM aerlive_bucuresti WHERE status='true'")
    stations = []
    st_names: set = set()
    for r in station_rows:
        try:
            lat, lng = round(float(r["lat"]), 4), round(float(r["long"]), 4)
        except (TypeError, ValueError):
            continue
        name = r["name"] or ""
        if name and name not in st_names:
            stations.append({"name": name, "lat": lat, "lng": lng})
            st_names.add(name)

    selected = _pit_days(con, "aerlive_bucuresti_version", days)
    if not selected:
        return {"dates": [], "stations": stations, "snaps": []}

    all_vers = _bulk_pit(
        con, "aerlive_bucuresti_version",
        "v.name AS n, v.pm25 AS pm25, v.pm10 AS pm10, v.status AS st",
    )
    by_item = _item_histories(all_vers)

    snaps = []
    for day in selected:
        snap: dict = {}
        for vers in by_item.values():
            r = _lookup(vers, day)
            if r is None or r["st"] != "true":
                continue
            name = r["n"] or ""
            try:
                pm25 = round(float(r["pm25"]), 1) if r["pm25"] else None
                pm10 = round(float(r["pm10"]), 1) if r["pm10"] else None
            except (TypeError, ValueError):
                continue
            if pm25 and 0 < pm25 < 500:
                snap[name] = [pm25, pm10 or 0]
        snaps.append(snap)

    return {"dates": selected, "stations": stations, "snaps": snaps}


# ---------- trafic frontiere — trends ----------

def trafic_daily_avg(con: sqlite3.Connection, days: int = 60) -> list[dict]:
    """Daily average wait (minutes) over the most-recent `days` days in the DB."""
    return rows(
        con,
        """SELECT date(c.commit_at) AS day,
                  round(avg(CAST(v.Timp AS REAL)), 1) AS avg_min
             FROM trafic_frontiere_version v
             JOIN commits c ON c.id = v._commit
             WHERE v.Timp != '' AND CAST(v.Timp AS INTEGER) > 0
               AND v.Status != 'Inchis'
               AND c.commit_at >= (
                     SELECT date(max(c2.commit_at), ?)
                     FROM commits c2 WHERE c2.id IN (SELECT _commit FROM trafic_frontiere_version)
                   )
             GROUP BY day
             ORDER BY day""",
        (f"-{days} day",),
    )


def trafic_hour_dow_heatmap(con: sqlite3.Connection) -> list[list[float | None]]:
    """7×24 matrix[dow][hour] of avg wait minutes (0=Sun … 6=Sat), all available data."""
    data = rows(
        con,
        """SELECT CAST(strftime('%w', c.commit_at) AS INTEGER) AS dow,
                  CAST(strftime('%H', c.commit_at) AS INTEGER) AS hour,
                  round(avg(CAST(v.Timp AS REAL)), 1) AS avg_min
             FROM trafic_frontiere_version v
             JOIN commits c ON c.id = v._commit
             WHERE v.Timp != '' AND CAST(v.Timp AS INTEGER) > 0
               AND v.Status != 'Inchis'
             GROUP BY dow, hour""",
    )
    matrix: list[list[float | None]] = [[None] * 24 for _ in range(7)]
    for r in data:
        d, h = r["dow"], r["hour"]
        if 0 <= d < 7 and 0 <= h < 24:
            matrix[d][h] = r["avg_min"]
    return matrix


# ---------- cmteb — trends ----------

def cmteb_status_over_time(con: sqlite3.Connection, days: int = 90) -> dict:
    """Returns {days, by_status} pivoted, covering last `days` days of CMTEB data."""
    raw = rows(
        con,
        """SELECT date(c.commit_at) AS day, v.status, count(*) AS n
             FROM cmteb_version v
             JOIN commits c ON c.id = v._commit
             WHERE c.commit_at >= (
                     SELECT date(max(c2.commit_at), ?)
                     FROM commits c2 WHERE c2.id IN (SELECT _commit FROM cmteb_version)
                   )
             GROUP BY day, v.status
             ORDER BY day""",
        (f"-{days} day",),
    )
    # collect all days and all statuses
    days_set: dict[str, None] = {}
    by_status: dict[str, dict[str, int]] = {}
    for r in raw:
        days_set[r["day"]] = None
        by_status.setdefault(r["status"], {})[r["day"]] = r["n"]
    sorted_days = sorted(days_set.keys())
    return {"days": sorted_days, "by_status": by_status}


# ---------- calitate aer — trends ----------

def aer_bucuresti_trend(con: sqlite3.Connection, days: int = 60) -> list[dict]:
    """Daily avg PM2.5 for Bucharest sensors over the most-recent `days` days in DB."""
    return rows(
        con,
        """SELECT date(c.commit_at) AS day,
                  round(avg(CAST(v.pm25 AS REAL)), 2) AS avg_pm25
             FROM aerlive_bucuresti_version v
             JOIN commits c ON c.id = v._commit
             WHERE v.status = 'true' AND v.pm25 != ''
               AND CAST(v.pm25 AS REAL) BETWEEN 0.1 AND 500
               AND c.commit_at >= (
                     SELECT date(max(c2.commit_at), ?)
                     FROM commits c2 WHERE c2.id IN (SELECT _commit FROM aerlive_bucuresti_version)
                   )
             GROUP BY day
             ORDER BY day""",
        (f"-{days} day",),
    )


# ---------- calitate aer ----------

def aer_iasi_snapshot(con: sqlite3.Connection) -> list[dict]:
    """Most-recent row per sensor id."""
    return rows(
        con,
        """SELECT a.id, a.latitude, a.longitude, a.note,
                  a.avg_pm25, a.avg_pm10, a.avg_pm1,
                  a.avg_temperature, a.avg_humidity, a.aqi, a.timelast
             FROM calitate_aer_iasi a
             JOIN (
               SELECT id, max(_commit) AS mc FROM calitate_aer_iasi GROUP BY id
             ) m ON m.id = a.id AND m.mc = a._commit""",
    )


def aer_bucuresti_snapshot(con: sqlite3.Connection) -> list[dict]:
    return rows(
        con,
        """SELECT name, lat, long, pm1, pm25, pm10, no2, ica, status
             FROM aerlive_bucuresti
             WHERE status = 'true'""",
    )


# ---------- energie ----------

def energie_enel_active(con: sqlite3.Connection) -> list[dict]:
    return rows(
        con,
        """SELECT provincia, comune, causa_disa, num_cli_di,
                  data_inter, data_prev_, Lat, Long, descrizion
             FROM energie_intreruperi_enel""",
    )


def energie_deer_slider(con: sqlite3.Connection, days: int = 90) -> dict:
    """Returns {dates, snaps} for DEER outages.

    DEER rows are tied directly to a commit (not versioned by item), so for
    each selected day we take all rows from the last commit of that day.
    snap format: [[județ, numar_lucrare, data_inceput, data_sfarsit, zona], ...]
    """
    # Last N distinct days with DEER data
    day_rows = con.execute(
        """SELECT date(c.commit_at) AS day, max(c.id) AS last_commit
             FROM commits c
            WHERE c.id IN (SELECT DISTINCT _commit FROM energie_deer_incidente)
            GROUP BY date(c.commit_at)
            ORDER BY day DESC
            LIMIT ?""",
        (days,),
    ).fetchall()

    if not day_rows:
        return {"dates": [], "snaps": []}

    day_rows = list(reversed(day_rows))
    dates = [r[0] for r in day_rows]

    snaps = []
    for _, commit_id in day_rows:
        snap_rows = con.execute(
            """SELECT "JUDEȚ", "NUMAR LUCRARE", "DATA ÎNCEPERE", "DATA FINALIZARE", zona
                 FROM energie_deer_incidente
                WHERE _commit = ?
                ORDER BY "JUDEȚ", "NUMAR LUCRARE" """,
            (commit_id,),
        ).fetchall()
        snaps.append([[r[0] or "", r[1] or "", r[2] or "", r[3] or "", r[4] or ""] for r in snap_rows])

    return {"dates": dates, "snaps": snaps}
