from typing import Optional, TYPE_CHECKING

import pandas as pd

from flask import Response
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, FormField, FieldList
from wtforms.validators import Length, Optional as OptionalValidator, DataRequired

from limbless_db import models

from .... import logger, db  # noqa F401
from ...TableDataForm import TableDataForm
from ...HTMXFlaskForm import HTMXFlaskForm
from .BarcodeInputForm import BarcodeInputForm


if TYPE_CHECKING:
    current_user: models.User = None    # type: ignore
else:
    from flask_login import current_user


class PoolMappingSubForm(FlaskForm):
    raw_label = StringField("Raw Label", validators=[OptionalValidator()])
    
    new_pool_name = StringField("Pool Name", validators=[DataRequired(), Length(min=4, max=models.Pool.name.type.length)])
    num_m_reads_requested = FloatField("Number of M Reads Requested", validators=[OptionalValidator()])


class PoolMappingForm(HTMXFlaskForm, TableDataForm):
    _template_path = "workflows/library_annotation/sas-1.2.html"

    pool_forms = FieldList(FormField(PoolMappingSubForm), label="Pool Mapping")
    contact_name = StringField("Contact Name", validators=[DataRequired(), Length(max=models.Contact.name.type.length)])
    contact_email = StringField("Contact Email", validators=[DataRequired(), Length(max=models.Contact.email.type.length)])
    contact_phone = StringField("Contact Phone", validators=[DataRequired(), Length(max=models.Contact.phone.type.length)])

    def __init__(self, seq_request: models.SeqRequest, uuid: str, formdata: dict = {}, previous_form: Optional[TableDataForm] = None):
        HTMXFlaskForm.__init__(self, formdata=formdata)
        TableDataForm.__init__(self, uuid=uuid, dirname="library_annotation", previous_form=previous_form)
        self.seq_request = seq_request
        self._context["seq_request"] = seq_request
        self.library_table = self.tables["library_table"]
        self.raw_pool_labels = self.library_table["pool"].unique().tolist()

        for i, pool in enumerate(self.raw_pool_labels):
            if i > len(self.pool_forms) - 1:
                self.pool_forms.append_entry()

            sub_form: PoolMappingSubForm = self.pool_forms[i]  # type: ignore
            sub_form.raw_label.data = str(pool)
            if not sub_form.new_pool_name.data:
                sub_form.new_pool_name.data = str(pool)

    def validate(self, user: models.User) -> bool:
        if not super().validate():
            return False

        pool_table_data = {
            "pool_name": [],
            "pool_label": [],
            "pool_id": [],
            "num_m_reads_requested": [],
        }

        def add_pool(name: str, label: str, pool_id: Optional[int], num_m_reads_requested: Optional[float]):
            pool_table_data["pool_name"].append(name)
            pool_table_data["pool_id"].append(pool_id)
            pool_table_data["pool_label"].append(label)
            pool_table_data["num_m_reads_requested"].append(num_m_reads_requested)

        sub_form: PoolMappingSubForm
        for sub_form in self.pool_forms:  # type: ignore
            # if sub_form.new_pool_name.data and sub_form.existing_pool.selected.data:
            #     sub_form.existing_pool.selected.errors = ["Define new pool or select an existing pool, not both."]
            #     sub_form.new_pool_name.errors = ["Define new pool or select an existing pool, not both."]
            #     return False
            
            # if not sub_form.new_pool_name.data and not sub_form.existing_pool.selected.data:
            #     sub_form.new_pool_name.errors = ["Define new pool or select an existing pool."]
            #     sub_form.existing_pool.selected.errors = ["Define new pool or select an existing pool."]
            #     return False
            
            if sub_form.new_pool_name.data:
                sub_form.new_pool_name.data = sub_form.new_pool_name.data.strip()
                if sub_form.new_pool_name.data in [pool.name for pool in user.pools]:
                    sub_form.new_pool_name.errors = ["You already have a pool with this name."]
                    return False

                add_pool(
                    name=sub_form.new_pool_name.data,
                    label=sub_form.raw_label.data,  # type: ignore
                    pool_id=None,
                    num_m_reads_requested=sub_form.num_m_reads_requested.data,
                )
            # elif sub_form.existing_pool.selected.data:
            #     if (pool := db.get_pool(int(sub_form.existing_pool.seleted.data))) is None:
            #         logger.error(f"Pool with ID {sub_form.existing_pool.seleted.data} not found.")
            #         raise Exception(f"Pool with ID {sub_form.existing_pool.seleted.data} not found.")
            #     add_pool(
            #         name=pool.name,
            #         label=sub_form.raw_label.data,  # type: ignore
            #         pool_id=pool.id,
            #         num_m_reads_requested=sub_form.num_m_reads_requested.data,
            #     )

        self.pool_table = pd.DataFrame(pool_table_data)
        return True

    def process_request(self, user: models.User) -> Response:
        if not self.validate(user=user):
            return self.make_response()

        self.metadata["pool_contact_name"] = self.contact_name.data
        self.metadata["pool_contact_email"] = self.contact_email.data
        self.metadata["pool_contact_phone"] = self.contact_phone.data
        self.add_table("pool_table", self.pool_table)
        self.update_data()

        barcode_input_form = BarcodeInputForm(
            seq_request=self.seq_request,
            uuid=self.uuid,
            previous_form=self,
        )
        return barcode_input_form.make_response()
