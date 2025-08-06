from typing import Optional

from flask import Response, url_for, flash
from flask_htmx import make_response

from opengsync_db import models
from opengsync_db.categories import MUXType

from ....tools import utils
from ....tools.spread_sheet_components import TextColumn, IntegerColumn
from ..common.CommonFlexMuxForm import CommonFlexMuxForm


class LibraryReMuxForm(CommonFlexMuxForm):
    _template_path = "workflows/library_remux/flex_annotation.html"
    _workflow_name = "library_remux"
    library: models.Library

    allowed_barcodes = [f"BC{i:03}" for i in range(1, 17)]
    mux_type = MUXType.TENX_FLEX_PROBE

    def __init__(self, library: models.Library, formdata: dict | None = None, uuid: Optional[str] = None):
        CommonFlexMuxForm.__init__(
            self, uuid=uuid, formdata=formdata, workflow=LibraryReMuxForm._workflow_name,
            seq_request=None, library=library, lab_prep=None, columns=[
                IntegerColumn("sample_id", "Sample ID", 100, required=True, read_only=True),
                IntegerColumn("library_id", "Library ID", 100, required=True, read_only=True),
                TextColumn("sample_name", "Demultiplexed Name", 300, required=True, read_only=True),
                TextColumn("barcode_id", "Bardcode ID", 200, required=False, max_length=models.links.SampleLibraryLink.MAX_MUX_FIELD_LENGTH, clean_up_fnc=CommonFlexMuxForm.padded_barcode_id),
            ]
        )

    def process_request(self) -> Response:
        if not self.validate():
            return self.make_response()
        
        self.flex_table["mux_barcode"] = utils.map_columns(self.flex_table, self.df, ["sample_id", "library_id"], "barcode_id")

        CommonFlexMuxForm.update_barcodes(sample_table=self.flex_table)

        self.complete()
        flash("Changes saved!", "success")
        return make_response(redirect=(url_for("libraries_page.library", library_id=self.library.id)))