from flask import Blueprint, render_template, redirect, request, url_for

libraries_page_bp = Blueprint("libraries_page", __name__)

from ... import db, forms, logger
from ...core import DBSession

@libraries_page_bp.route("/libraries")
def libraries_page():
    with DBSession(db.db_handler) as session:
        libraries = session.get_libraries()
        n_pages = int(session.get_num_libraries() / 20)

    return render_template(
        "libraries_page.html", libraries=libraries,
        n_pages=n_pages, page=0
    )

@libraries_page_bp.route("/libraries/<int:library_id>")
def library_page(library_id):
    with DBSession(db.db_handler) as session:
        library = session.get_library(library_id)
        if not library:
            return redirect("/libraries")
        
        library.samples = session.get_library_samples(library.id)

    library_form = forms.LibraryForm()
    library_form.name.data = library.name
    library_form.library_type.data = str(library.library_type_id)
    library_form.index_kit.data = library.index_kit_id

    sample_form = forms.SampleForm()
    
    return render_template(
        "library_page.html", library=library,
        library_form=library_form,
        common_indexkits=db.common_kits,
        selected_kit=library.index_kit,
        sample_form=sample_form,
        common_organisms=db.common_organisms,
        selected_organism="",
        show_indices=True
    )