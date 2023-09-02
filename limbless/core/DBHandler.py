import os
from typing import Optional, Union

from sqlmodel import create_engine, SQLModel, Session, select
from sqlalchemy import orm

from .. import models
from . import categories
from ..sample_experiment import create_sample_experiment
from ..index_kits import add_index_kits

class DBHandler():
    def __init__(self, db_path, create_admin: bool = True, load_sample_data: bool = False):
        if not os.path.exists(os.path.dirname(db_path)) and db_path != ":memory:":
            os.mkdir(os.path.dirname(db_path))

        if os.path.exists(db_path):
            load_sample_data = False

        self._engine = create_engine(f"sqlite:///{db_path}?check_same_thread=False")
        self._session: Optional[orm.Session] = None

        SQLModel.metadata.create_all(self._engine)

        if create_admin:
            self.open_session()
            self.__admin = self._session.get(models.User, 1)
            if not self.__admin:
                self.__admin = models.User(
                    email="admin", password="password",
                    role=categories.UserRole.ADMIN.id
                )
            self._session.add(self.__admin)
            self.close_session(commit=True)

        if load_sample_data:
            add_index_kits(self)
            create_sample_experiment(self)


    def open_session(self) -> None:
        self._session = Session(self._engine, expire_on_commit=False)
    
    def close_session(self, commit=True) -> None:
        if commit:
            self._session.commit()
        self._session.close()
        self._session = None

    from .model_handlers._project_methods import (
        create_project, get_project, get_projects,
        update_project, delete_project, get_project_by_name,
        get_num_projects
    )

    from .model_handlers._experiment_methods import (
        create_experiment, get_experiment, get_experiments,
        update_experiment, delete_experiment, get_experiment_by_name,
        get_num_experiments
    )

    from .model_handlers._sample_methods import (
        create_sample, get_sample, get_samples,
        delete_sample, update_sample, get_sample_by_name,
        get_num_samples
    )

    from .model_handlers._run_methods import (
        create_run, get_run, get_runs,
        update_run, delete_run,
        get_run_num_samples,
        get_num_runs
    )

    from .model_handlers._library_methods import (
        create_library, get_library, get_libraries,
        delete_library, update_library, get_library_by_name,
        get_num_libraries
    )

    from .model_handlers._user_methods import (
        create_user, get_user, get_users,
        delete_user, update_user,
        get_user_by_email
    )

    from .model_handlers._organism_methods import (
        create_organism, get_organism, get_organisms,
        get_organisms_by_name, query_organisms,
        get_num_organisms
    )

    from .model_handlers._seqindex_methods import (
        create_seqindex, get_seqindex, get_seqindices_by_adapter
    )

    from .model_handlers._seqkit_methods import (
        create_seqkit, get_seqkit, get_seqkit_by_name
    )

    from .model_handlers._link_methods import (
        get_project_samples,
        get_project_users,
        get_run_libraries,
        get_library_samples,
        get_library_runs,
        get_user_projects,
        get_sample_libraries,
        
        get_experiment_data,
        get_run_data,

        get_experiment_runs,

        link_project_user,
        link_library_sample,
        link_run_library,
        link_sample_index,

        unlink_library_sample,
        unlink_run_library,
        unlink_project_user
    )

            
    