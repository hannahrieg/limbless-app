from typing import Any, Optional

from flask import Response, flash, url_for
from flask_htmx import make_response
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired, Length

from limbless_db import models
from limbless_db.categories import LibraryType, GenomeRef, LibraryStatus
from ... import db, logger  # noqa: F401
from ..HTMXFlaskForm import HTMXFlaskForm


class LibraryForm(HTMXFlaskForm):
    _template_path = "forms/library.html"
    _form_label = "library_form"

    name = StringField("Name", validators=[DataRequired(), Length(min=3, max=models.Library.name.type.length)])
    library_type = SelectField("Library Type", choices=LibraryType.as_selectable(), coerce=int)
    genome = SelectField("Reference Genome", choices=GenomeRef.as_selectable(), coerce=int)
    status = SelectField("Status", choices=LibraryStatus.as_selectable(), coerce=int)

    def __init__(self, library: models.Library, formdata: Optional[dict[str, Any]] = None):
        super().__init__(formdata=formdata)
        self.library = library
        if formdata is None:
            self.__fill_form(library)

    def __fill_form(self, library: models.Library):
        self.name.data = library.name
        self.library_type.data = library.type_id
        self.genome.data = library.genome_ref_id
        self.status.data = library.status_id
    
    def process_request(self) -> Response:
        if not self.validate():
            return self.make_response()

        self.library.name = self.name.data   # type: ignore
        self.library.type = LibraryType.get(int(self.library_type.data))
        self.library.genome_ref = GenomeRef.get(self.genome.data)
        self.library.status = LibraryStatus.get(self.status.data)

        self.library = db.update_library(self.library)
        
        flash(f"Updated library '{self.library.name}'.", "success")

        return make_response(
            redirect=url_for("libraries_page.library_page", library_id=self.library.id),
        )