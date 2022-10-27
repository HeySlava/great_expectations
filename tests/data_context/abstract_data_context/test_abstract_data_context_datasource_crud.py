from typing import Optional, Union
from unittest import mock

import pytest

from great_expectations.data_context import AbstractDataContext
from great_expectations.data_context.data_context_variables import (
    DataContextVariables,
    EphemeralDataContextVariables,
)
from great_expectations.data_context.store import DatasourceStore
from great_expectations.data_context.types.base import (
    DataContextConfig,
    DatasourceConfig,
)
from great_expectations.datasource import BaseDatasource, LegacyDatasource


class StubDatasourceStore(DatasourceStore):
    """Used for mocking the set() call."""

    def __init__(self):
        pass


class FakeAbstractDataContext(AbstractDataContext):
    def __init__(self):
        """Override __init__ with only the needed attributes."""
        self._datasource_store = StubDatasourceStore()
        self._variables: Optional[DataContextVariables] = None
        self._cached_datasources: dict = {}
        self._usage_statistics_handler = None

    def _init_variables(self):
        """Using EphemeralDataContextVariables to store in memory."""
        return EphemeralDataContextVariables(config=DataContextConfig())

    def _determine_substitutions(self):
        """No substitutions required for these tests."""
        return {}

    def save_expectation_suite(self):
        """Abstract method. Only a stub is needed."""
        pass

    def _init_datasource_store(self):
        """Abstract method. Only a stub is needed."""
        pass


@pytest.mark.unit
def test_save_datasource_empty_store(datasource_config_with_names: DatasourceConfig):

    context = FakeAbstractDataContext()
    # Make sure the fixture has the right configuration
    assert len(context.list_datasources()) == 0

    # add_datasource used to create a datasource object for use in save_datasource
    datasource_to_save = context.add_datasource(
        **datasource_config_with_names.to_json_dict(), save_changes=False
    )

    with mock.patch(
        "great_expectations.data_context.store.datasource_store.DatasourceStore.set",
        autospec=True,
        return_value=datasource_config_with_names,
    ) as mock_set:

        saved_datasource: Union[
            LegacyDatasource, BaseDatasource
        ] = context.save_datasource(datasource_to_save)

    mock_set.assert_called_once()

    # Make sure the datasource config got into the context config
    assert len(context.list_datasources()) == 1
    assert (
        context.config.datasources[datasource_to_save.name]
        == datasource_config_with_names
    )

    # Make sure the datasource got into the cache
    assert len(context._cached_datasources) == 1

    # Make sure the stored and returned datasource is the same one as the cached datasource
    cached_datasource = context._cached_datasources[datasource_to_save.name]
    assert saved_datasource == cached_datasource


@pytest.mark.unit
def test_save_datasource_overwrites_on_name_collision(
    datasource_config_with_names: DatasourceConfig,
):

    context = FakeAbstractDataContext()
    # Make sure the fixture has the right configuration
    assert len(context.list_datasources()) == 0

    # add_datasource used to create a datasource object for use in save_datasource
    datasource_to_save = context.add_datasource(
        **datasource_config_with_names.to_json_dict(), save_changes=False
    )

    with mock.patch(
        "great_expectations.data_context.store.datasource_store.DatasourceStore.set",
        autospec=True,
        return_value=datasource_config_with_names,
    ) as mock_set:

        context.save_datasource(datasource_to_save)

        assert len(context.list_datasources()) == 1
        assert len(context._cached_datasources) == 1

        # Let's re-save
        context.save_datasource(datasource_to_save)

        # Make sure we still only have 1 datasource
        assert len(context.list_datasources()) == 1
        assert len(context._cached_datasources) == 1

    assert mock_set.call_count == 2