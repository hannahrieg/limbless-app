from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import current_user, login_required

from ... import forms, models, db, logger, PAGE_LIMIT
from ...core import DBSession

feature_kits_page_bp = Blueprint("feature_kits_page", __name__)


@feature_kits_page_bp.route("/feature_kit")
@login_required
def feature_kits_page():
    with DBSession(db.db_handler) as session:
        feature_kits, n_pages = session.get_feature_kits(limit=PAGE_LIMIT)

    return render_template(
        "feature_kits_page.html",
        feature_kits=feature_kits, feature_kits_n_pages=n_pages, feature_kits_active_page=0,
    )


@feature_kits_page_bp.route("/feature_kit/<int:feature_kit_id>")
@login_required
def feature_kit_page(feature_kit_id: int):
    with DBSession(db.db_handler) as session:
        feature_kit = session.get_feature_kit(feature_kit_id)

    path_list = [
        ("Feature Kits", url_for("feature_kits_page.feature_kits_page")),
        (f"{feature_kit_id}", ""),
    ]

    features, features_n_pages = session.get_features(feature_kit_id=feature_kit_id, limit=PAGE_LIMIT)

    return render_template(
        "feature_kit_page.html",
        path_list=path_list,
        feature_kit=feature_kit,
        features=features,
        features_n_pages=features_n_pages,
        features_active_page=0,
        features_current_sort="id",
        features_current_sort_order="desc",
    )