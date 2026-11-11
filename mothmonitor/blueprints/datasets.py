from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, Response
from flask_security import permissions_required, auth_required, current_user

from sqlalchemy.orm import joinedload, attributes

import csv
from io import StringIO
from datetime import datetime

from ..models import db, Device, Night, has_stale_night

from .. import antenna
from ..s3_storage import S3Reader, enqueue_refresh_nights, config_parsed


datasets = Blueprint('datasets', __name__)


@datasets.route('/detail/<night_id>')
@auth_required()
def night_detail(night_id):
    night = db.get_or_404(Night, night_id)
    if night.last_photo:
        last_photo_url = S3Reader().read_url(current_app.config['S3_BUCKET'], night.last_photo)
    return render_template("datasets/hx/detail_row.html", **locals())

def sort_args():
    sort = request.args.get('sort', 'last_modified')
    sort_asc = request.args.get('asc', False)
    return sort, sort_asc

def select_nights():

    sort, sort_asc = sort_args()
    
    select = db.select(Night).options(joinedload(Night.device))
    sorts = []
    if sort:
        sorter = getattr(Night, sort)
        if not sort_asc:
            sorter = sorter.desc()
        sorts.append(sorter)
        if sort == 'device_id':
            sorts.append(Night.night.desc())
        select = select.order_by(*sorts)
    if current_user.can("site") and not current_user.can("research"):
        ids = [x.id for x in current_user.site_devices]
        # restrict query to assigned devices
        select = select.join(Night.device).filter(Device.id.in_(ids))

    filters = { k: request.args.get(k) for k in request.args.keys() if k.startswith("f_") and request.args.get(k) not in ("", None, "0") }
    if filters:
        if filters.get("f_attract"):
            select = select.filter(Night.config[("parsed", "attracts")].as_integer() == int(filters.get("f_attract")))
        if filters.get("f_sessions"):
            select = select.filter(Night.config[("parsed", "num_hours")].as_integer() == int(filters.get("f_sessions")))
        if filters.get("f_min_hours"):
            select = select.filter(Night.config[("parsed", "total_hours")].as_float() >= float(filters.get("f_min_hours")))
        if filters.get("f_min_photos"):
            select = select.filter(Night.photo_count >= int(filters.get("f_min_photos")))
        if filters.get("f_station"):
            select = select.join(Night.device).filter(Device.antenna_deployment == int(filters.get("f_station")))
    return select


@datasets.route('/list')
@auth_required()
def list_nights():
    forced_refresh = request.args.get('refresh')
    if forced_refresh or has_stale_night():
         enqueue_refresh_nights(forced_refresh=forced_refresh)
    else:
        try:
            syncs = antenna.enqueue_sync_stale_deployments()    
            if len(syncs):
                flash(f"Syncing {len(syncs)} stations on Antenna", "ok")
        except antenna.APIError as e:
            flash(f"{e}", "error")
         
    sort, sort_asc = sort_args()

    select = select_nights()
            
    nights = db.paginate(select, per_page=20, error_out=False)

    stations = []
    for d in db.session.execute(Device.select_active().filter(Device.antenna_deployment != None)).scalars():
        stations.append({"id": str(d.antenna_deployment), "name": d.antenna_deployment_name})
    
    if nights.page != 1 and len(nights.items) == 0:
        return redirect(url_for(request.endpoint, page=1))

    qc_reasons = {
        "": "",
        "black": "All black",
        "banded": "Banded",
        "blurry": "Blurry",
        "other": "Other"
    }
    
    return render_template("datasets/list_nights.html", nights=nights, sort=sort, sort_asc=sort_asc, station_url=antenna.station_url, stations=stations, qc_reasons=qc_reasons)

@datasets.route('/qc/<night_id>', methods=["POST"])
@permissions_required("admin")
def night_qc(night_id):
    night = db.get_or_404(Night, night_id)
    reason = request.form.get('qc_reason')
    night.qc_reason = reason
    night.qc_by = current_user.name
    db.session.commit()
    return "<span id='qc_status' hx-swap-oob='true' class='fading'>&#x2705;</span>"

def generate_csv(headers, dataset):
    data = StringIO()
    w = csv.writer(data)

    def yield_clear():
        d = data.getvalue()
        data.seek(0)
        data.truncate(0)
        return d
    
    # write header
    w.writerow(headers)
    yield yield_clear()
    
    # write each item
    for item in dataset:
        row = [item[x] for x in headers]
        w.writerow(row)
        yield yield_clear()

@datasets.route('/download')
@auth_required()
def download():
    select = select_nights()

    nights = db.session.execute(select).scalars()

    nights_data = []
    for n in nights:
        config = n.config.get("parsed", {})
        
        n_data = {
                "device_id": n.device_id,
                "device_label": n.device.label,
                "night": n.night.strftime("%A, %b %-d %Y"),
                "night_date": n.night.strftime("%F"),
                "upload_date": n.last_modified and n.last_modified.strftime("%F") or "",
                "photo_count": n.photo_count,
                "attract_lights": config.get("attracts"),
                "qc_flag": n.qc_reason,
                "qc_by": n.qc_by,
                "session_hours": n.config.get("schedule", {}).get("hour"),
                "session_minute": n.config.get("schedule", {}).get("minute"),
                "session_interval": n.config.get("schedule", {}).get("camera_interval"),
                "session_runtime": n.config.get("schedule", {}).get("runtime"),
                "session_count": config.get("num_hours"),
                "hours_total": config.get("total_hours"),
                "antenna_station_id": n.device.antenna_deployment,
            }
        # sampled hours
        hours = config.get("hours", [])
        minute = int(n.config.get("schedule", {}).get("minute", 0))
        runtime_extent = minute + int(n.config.get("schedule", {}).get("runtime", 0))
        def compute_hour_min(hr):
            if hr in hours:
                return 60-minute
            x = runtime_extent - 60
            rd = 1
            while x > 0:
                if hr in [(y+rd)%24 for y in hours]:
                    return min(60, x)
                rd = rd+1
                x = x-60
            return 0
        for h in list(range(19,24)) + list(range(0,7)):
            n_data[f"sampled_hour_{h}"] = compute_hour_min(h)
        nights_data.append(n_data)

    headers = nights_data[0].keys()
    # stream the response as the data is generated
    response = Response(generate_csv(headers, nights_data), mimetype='text/csv')
    # add a filename
    filename = f"MMM_dataset_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
    response.headers.set("Content-Disposition", "attachment", filename=filename)
    return response

@datasets.route("/_migrate/config_parsed")
@permissions_required("admin")
def migrate_config_parsed():

    for night in db.session.execute(db.select(Night)).scalars():
        night.config = config_parsed(night.config or {})
        attributes.flag_modified(night, "config")
    db.session.commit()
    return "ok"
