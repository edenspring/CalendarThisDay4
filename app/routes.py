from datetime import datetime, timedelta
from flask import (Blueprint, render_template, redirect, url_for)
from app.forms import AppointmentForm
import sqlite3
import os
bp = Blueprint("main", __name__, url_prefix='/')
DB_FILE = os.environ.get("DB_FILE")

def round_time(time):
    return time - timedelta(minutes=time.minute % 15,
                            seconds=time.second)

@bp.route('/', methods=("GET","POST"))
def main():
    d = datetime.now()
    return redirect(url_for(".daily", year=d.year, month=d.month, day=d.day))

@bp.route("/<int:year>/<int:month>/<int:day>", methods=["GET", "POST"])
def daily(year, month, day):
    form = AppointmentForm()
    if form.validate_on_submit():
        with sqlite3.connect(DB_FILE) as conn:
            curs = conn.cursor()
            sql = """
                    INSERT INTO appointments (
                        name,
                        start_datetime,
                        end_datetime,
                        description,
                        private
                    )
                    VALUES
                    (
                        :name,
                        :start_datetime,
                        :end_datetime,
                        :description,
                        :private
                    )
                """
            params = {
                    'name': form.name.data,
                    'start_datetime': round_time(datetime.combine(
                                        form.start_date.data,
                                        form.start_time.data,
                                      )),
                    'end_datetime': round_time(datetime.combine(
                                        form.end_date.data,
                                        form.end_time.data,
                                    )),
                    'description': form.description.data,
                    'private': form.private.data
                    }
            curs.execute(sql, params)    
    with sqlite3.connect(DB_FILE) as conn:
        curs = conn.cursor()
        day = datetime(year, month, day)
        next_day = day + timedelta(days=1)
        curs.execute("""
                    SELECT id, name, start_datetime, end_datetime
                    FROM appointments
                    WHERE start_datetime BETWEEN :day AND :next_day
                    ORDER BY start_datetime
                    """, {'day': day, 'next_day': next_day})
        data = curs.fetchall()
        rows = []
        for row in data:
            start = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S')
            rows.append(([row[0], row[1], start, end]))
        return render_template('main.html', rows=rows, form=form)
