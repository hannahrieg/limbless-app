from typing import Optional

from flask import Response, flash, url_for
from flask_htmx import make_response
from wtforms import StringField, IntegerField, SelectField, FormField
from wtforms.validators import DataRequired, Length, NumberRange, Optional as OptionalValidator

from ..HTMXFlaskForm import HTMXFlaskForm
from ...categories import FlowCellType
from ... import db, logger, models
from ..SearchBar import SearchBar


class ExperimentForm(HTMXFlaskForm):
    _template_path = "forms/experiment.html"
    _form_label = "experiment_form"

    sequencer = FormField(SearchBar, label="Select Sequencer", description="Select the sequencer that will be used for sequencing.")
    flowcell_type = SelectField(
        "Flowcell Type", choices=FlowCellType.as_selectable(),
        validators=[DataRequired()],
        description="Type of flowcell to use for sequencing."
    )
    flowcell = StringField("Flowcell ID", validators=[DataRequired(), Length(min=3, max=64)])
    num_lanes = IntegerField("Number of Lanes", default=1, validators=[DataRequired(), NumberRange(min=1, max=8)])
    
    r1_cycles = IntegerField("R1 Cycles", validators=[DataRequired()])
    r2_cycles = IntegerField("R2 Cycles", validators=[OptionalValidator()])
    i1_cycles = IntegerField("I1 Cycles", validators=[DataRequired()])
    i2_cycles = IntegerField("I2 Cycles", validators=[OptionalValidator()])

    sequencing_person = FormField(SearchBar, label="Sequencing Person")

    def __init__(self, user: Optional[models.User] = None, formdata: Optional[dict] = None):
        HTMXFlaskForm.__init__(self, formdata=formdata)
        self.prepare(user)

    def prepare(self, user: Optional[models.User]):
        if user is not None:
            self.sequencing_person.selected.data = user.id
            self.sequencing_person.search_bar.data = user.search_name()

    def validate(self) -> bool:
        if (validated := super().validate()) is False:
            return False
        
        return validated
    
    def __update_existing_experiment(self, experiment: models.Experiment) -> Response:
        # TODO: check if lane is already in use when removing lanes
        experiment = db.db_handler.update_experiment(
            experiment_id=experiment.id,
            flowcell=self.flowcell.data,
            r1_cycles=self.r1_cycles.data,
            r2_cycles=self.r2_cycles.data,
            i1_cycles=self.i1_cycles.data,
            i2_cycles=self.i2_cycles.data,
            num_lanes=self.num_lanes.data,
            sequencer_id=self.sequencer.selected.data,
            sequencing_person_id=self.sequencing_person.selected.data,
        )

        logger.debug(f"Edited experiment on flowcell '{experiment.flowcell}'")
        flash(f"Edited experiment on flowcell '{experiment.flowcell}'.", "success")

        return make_response(redirect=url_for("experiments_page.experiment_page", experiment_id=experiment.id))

    def __create_new_experiment(self) -> Response:
        experiment = db.db_handler.create_experiment(
            flowcell=self.flowcell.data,
            sequencer_id=self.sequencer.data,
            r1_cycles=self.r1_cycles.data,
            r2_cycles=self.r2_cycles.data,
            i1_cycles=self.i1_cycles.data,
            i2_cycles=self.i2_cycles.data,
            num_lanes=self.num_lanes.data,
            sequencing_person_id=self.sequencing_person.selected.data
        )

        logger.debug(f"Created experiment on flowcell '{experiment.flowcell}'")
        flash(f"Created experiment on flowcell '{experiment.flowcell}'.", "success")

        return make_response(
            redirect=url_for("experiments_page.experiment_page", experiment_id=experiment.id),
        )

    def process_request(self, **context) -> Response:
        if not self.validate():
            return self.make_response(**context)
        
        experiment = context.get("experiment")

        if experiment is not None:
            return self.__update_existing_experiment(experiment)

        return self.__create_new_experiment()
    