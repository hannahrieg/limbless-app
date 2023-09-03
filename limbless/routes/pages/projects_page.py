from flask import Blueprint, render_template, redirect, request, url_for
from flask_login import login_required, current_user

projects_page_bp = Blueprint("projects_page", __name__)

from ... import db, forms, logger
from ...core import DBSession

@projects_page_bp.route("/projects")
@login_required
def projects_page():
    project_form = forms.ProjectForm()

    with DBSession(db.db_handler) as session:
        projects = session.get_projects()
        n_pages = int(session.get_num_projects() / 20)

    return render_template(
        "projects_page.html", project_form=project_form,
        projects=projects, n_pages=n_pages, active_page=0
    )

@projects_page_bp.route("/projects/<project_id>")
@login_required
def project_page(project_id):
    with DBSession(db.db_handler) as session:
        project = db.db_handler.get_project(project_id)
        if not project:
            return redirect("/projects") # TODO: redirect to 404 page
            
        samples = db.db_handler.get_project_samples(project_id)
    
    table_form = forms.SampleTableForm()
    with open("data/test.tsv", "r") as f:
        table_form.text.data = f.read()

    logger.debug(db.common_organisms)

    return render_template(
        "project_page.html", project=project,
        sample_form=forms.SampleForm(),
        samples=samples,
        table_form=table_form,
        common_organisms=db.common_organisms
    )