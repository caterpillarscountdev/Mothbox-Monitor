from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_security import auth_required, current_user

from sqlalchemy.orm import joinedload

from ..models import db, Device, Night, has_stale_night
from .. import antenna
from ..s3_storage import S3Reader, enqueue_refresh_nights


datasets = Blueprint('datasets', __name__)


@datasets.route('/detail/<night_id>')
@auth_required()
def night_detail(night_id):
    night = db.get_or_404(Night, night_id)
    if night.last_photo:
        last_photo_url = S3Reader().read_url(current_app.config['S3_BUCKET'], night.last_photo)
    return render_template("datasets/hx/detail_row.html", **locals())
    


@datasets.route('/list')
@auth_required()
def list_nights():
    forced_refresh = request.args.get('refresh')
    if forced_refresh or has_stale_night():
         enqueue_refresh_nights(forced_refresh=forced_refresh)

    try:
        syncs = antenna.enqueue_sync_stale_deployments()    
        if len(syncs):
            flash(f"Syncing {len(syncs)} stations on Antenna", "ok")
    except antenna.APIError as e:
        flash(f"{e}", "error")
         
    sort = request.args.get('sort', 'last_modified')
    sort_asc = request.args.get('asc', False)

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
    
    nights = db.paginate(select, per_page=20, error_out=False)

    if nights.page != 1 and len(nights.items) == 0:
        return redirect(url_for(request.endpoint, page=1))

    return render_template("datasets/list_nights.html", nights=nights, sort=sort, sort_asc=sort_asc, station_url=antenna.station_url)


