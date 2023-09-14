from flask import Blueprint, url_for, render_template, flash, abort
from flask_htmx import make_response
from flask_login import login_required, current_user

from .... import db, forms, logger
from ....core import DBSession
from ....categories import UserRole

seq_requests_htmx = Blueprint("seq_requests_htmx", __name__, url_prefix="/api/seq_requests/")


@login_required
@seq_requests_htmx.route("create", methods=["GET"])
def get(page: int):
    with DBSession(db.db_handler) as session:
        if current_user.role_type == UserRole.CLIENT:
            seq_requests = session.get_seq_requests(limit=20, offset=20 * page, user_id=current_user.id)
            n_pages = int(session.get_num_seq_requests(user_id=current_user.id) / 20)
        else:
            seq_requests = session.get_seq_requests(limit=20, offset=20 * page, user_id=None)
            n_pages = int(session.get_num_seq_requests(user_id=None) / 20)

    page = min(page, n_pages)

    return make_response(
        render_template(
            "components/tables/seq_request.html", seq_requests=seq_requests,
            n_pages=n_pages, active_page=page
        ), push_url=False
    )


@login_required
@seq_requests_htmx.route("<int:seq_request_id>/edit", methods=["POST"])
def edit(seq_request_id: int):
    if (seq_request := db.db_handler.get_seq_request(seq_request_id)) is None:
        return abort(404)

    if current_user.role_type == UserRole.CLIENT:
        if seq_request.requestor_id != current_user.id:
            return abort(403)

    seq_request_form = forms.SeqRequestForm()
    db.db_handler.update_seq_request(
        seq_request_id,
        name=seq_request_form.name.data,
        description=seq_request_form.description.data,
    )

    flash(f"Updated sequencing request '{seq_request.name}'", "success")
    logger.info(f"Updated sequencing request '{seq_request.name}'")

    return make_response(
        redirect=url_for("seq_requests_page.seq_request_page", seq_request_id=seq_request.id),
    )


@login_required
@seq_requests_htmx.route("<int:seq_request_id>/delete", methods=["GET"])
def delete(seq_request_id: int):
    if (seq_request := db.db_handler.get_seq_request(seq_request_id)) is None:
        return abort(404)

    if current_user.role_type == UserRole.CLIENT:
        if seq_request.requestor_id != current_user.id:
            return abort(403)

    db.db_handler.delete_seq_request(seq_request_id)

    flash(f"Deleted sequencing request '{seq_request.name}'", "success")
    logger.info(f"Deleted sequencing request '{seq_request.name}'")

    return make_response(
        redirect=url_for("seq_requests_page.seq_requests_page"),
    )


@login_required
@seq_requests_htmx.route("create", methods=["POST"])
def create():
    seq_request_form = forms.SeqRequestForm()

    if not seq_request_form.validate_on_submit():
        if seq_request_form.bioinformatician_name.data:
            if not seq_request_form.bioinformatician_email.data:
                seq_request_form.bioinformatician_email.errors.append("Bioinformatician email is required")
                seq_request_form.bioinformatician_email.flags.required = True
        template = render_template(
            "forms/seq_request/seq_request.html",
            seq_request_form=seq_request_form
        )
        return make_response(
            template, push_url=False
        )

    organization_name = seq_request_form.organization_name.data
    if seq_request_form.organization_department.data:
        organization_name += f" ({seq_request_form.organization_department.data})"

    contact_person = db.db_handler.create_contact(
        name=seq_request_form.contact_person_name.data,
        organization=organization_name,
        email=seq_request_form.contact_person_email.data,
        phone=seq_request_form.contact_person_phone.data,
        address=seq_request_form.organization_address.data,
    )

    billing_contact = db.db_handler.create_contact(
        name=seq_request_form.billing_contact.data,
        address=seq_request_form.billing_address.data,
        email=seq_request_form.billing_email.data,
        phone=seq_request_form.billing_phone.data,
        billing_code=seq_request_form.billing_code.data
    )

    if seq_request_form.bioinformatician_name.data:
        bioinformatician = db.db_handler.create_contact(
            name=seq_request_form.bioinformatician_name.data,
            email=seq_request_form.bioinformatician_email.data,
            phone=seq_request_form.bioinformatician_phone.data,
        )
        bioinformatician_contact_id = bioinformatician.id
    else:
        bioinformatician_contact_id = None

    seq_request = db.db_handler.create_seq_request(
        name=seq_request_form.name.data,
        description=seq_request_form.description.data,
        requestor_id=current_user.id,
        person_contact_id=contact_person.id,
        billing_contact_id=billing_contact.id,
        bioinformatician_contact_id=bioinformatician_contact_id,
    )

    flash(f"Created new sequencing request '{seq_request.name}'", "success")
    logger.info(f"Created new sequencing request '{seq_request.name}'")
    return make_response(
        redirect=url_for("seq_requests_page.seq_request_page", seq_request_id=seq_request.id),
    )


@login_required
@seq_requests_htmx.route("<int:seq_request_id>/add_library", methods=["POST"])
def add_library(seq_request_id: int):
    if (seq_request := db.db_handler.get_seq_request(seq_request_id)) is None:
        return abort(404)

    if seq_request.requestor_id != current_user.id:
        if current_user.role_type != UserRole.ADMIN:
            return abort(403)

    select_library_form = forms.SelectLibraryForm()

    if not select_library_form.validate_on_submit():
        template = render_template(
            "forms/seq_request/select_library.html",
            select_library_form=select_library_form
        )
        return make_response(
            template, push_url=False
        )
    
    library_id = select_library_form.library.data
    if (library := db.db_handler.get_library(library_id)) is None:
        return abort(404)
    
    _ = db.db_handler.link_library_seq_request(library_id, seq_request_id)

    flash(f"Added library '{library.name}' to sequencing request '{seq_request.name}'", "success")
    logger.debug(f"Added library '{library.name}' to sequencing request '{seq_request.name}'")

    return make_response(
        redirect=url_for("seq_requests_page.seq_request_page", seq_request_id=seq_request_id),
    )
