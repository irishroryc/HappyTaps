"""
    This code taken from https://gist.github.com/milen-yordanov/966a81790b183e48a2831aeec323f550

    Slack Bolt InstallationStore and OAuthStateStore implementation with Google Datastore.

    The following composite indices could be created, but they are not required.
    The code can work without them.

    - kind: SlackAppInstallation
    properties:
    - name: client_id
    - name: enterprise_id
    - name: team_id
    - name: user_id
    - name: installed_at
        direction: asc

    - kind: SlackAppBot
    properties:
    - name: client_id
    - name: enterprise_id
    - name: team_id
    - name: installed_at
        direction: asc
"""
#pylint: disable=line-too-long,missing-class-docstring,missing-function-docstring

import logging
from datetime import datetime, timezone, timedelta
from logging import Logger
from typing import Optional
from uuid import uuid4

from google.cloud import datastore
from google.cloud.datastore import Client, Entity
from slack_sdk.oauth import OAuthStateStore, InstallationStore
from slack_sdk.oauth.installation_store import Installation, Bot


def _to_timestamp(obj):
    if not obj:
        return obj

    if isinstance(obj, datetime):
        return obj.timestamp()

    return obj



class GoogleDatastoreInstallationStore(InstallationStore):
    datastore_client: Client
    _datastore_bot_kind: str
    _datastore_installation_kind: str
    _has_composite_index: bool
    client_id: str

    installation_exclude_from_indexes = [
        "bot_refresh_token",
        "bot_scopes",
        "enterprise_name",
        "enterprise_url",
        "team_name",
        "user_refresh_token",
        "user_scopes",
        "user_token",
        "incoming_webhook_url",
        "incoming_webhook_channel",
        "incoming_webhook_channel_id",
        "incoming_webhook_configuration_url",
    ]

    bot_exclude_from_indexes = [
        "bot_refresh_token",
        "bot_scopes",
        "bot_token",
        "enterprise_name",
        "team_name"
    ]


    def __init__(
        self,
        *,
        datastore_client: Client,
        datastore_bot_kind: str,
        datastore_installation_kind: str,
        client_id: str,
        logger: Logger,
        has_composite_index: bool = False
    ):
        self.datastore_client = datastore_client
        self.client_id = client_id
        self._logger = logger
        self._datastore_bot_kind = datastore_bot_kind
        self._datastore_installation_kind = datastore_installation_kind
        self._has_composite_index = has_composite_index


    @property
    def logger(self) -> Logger:
        if self._logger is None:
            self._logger = logging.getLogger(__name__)
        return self._logger


    @property
    def datastore_bot_kind(self) -> str:
        return self._datastore_bot_kind


    @property
    def datastore_installation_kind(self) -> str:
        return self._datastore_installation_kind


    def _generate_kind_new_key(self, kind):
        """" Generates a unique kind ID. """
        while True:
            new_id = str(uuid4())
            new_key = self.datastore_client.key(kind, new_id)
            entity = self.datastore_client.get(new_key)
            if entity is None:
                return new_key


    def save(self, installation: Installation):
        installation_dict = installation.to_dict()
        installation_dict["client_id"] = self.client_id

        query = self.datastore_client.query(kind=self.datastore_installation_kind)
        query.add_filter("client_id", "=", installation_dict["client_id"])
        query.add_filter("enterprise_id", "=", installation_dict["enterprise_id"])
        query.add_filter("team_id", "=", installation_dict["team_id"])
        query.add_filter("installed_at", "=", installation_dict["installed_at"])

        row_to_update = list(query.fetch(limit=1))

        if row_to_update:
            installation_entity = row_to_update[0]
        else:
            new_key = self._generate_kind_new_key(self.datastore_installation_kind)
            installation_entity: Entity = datastore.Entity(key=new_key, exclude_from_indexes=self.installation_exclude_from_indexes)

        installation_entity.update(**installation_dict)
        self.datastore_client.put(installation_entity)

        self.save_bot(installation.to_bot())


    def save_bot(self, bot: Bot):
        bot_dict = bot.to_dict()
        bot_dict["client_id"] = self.client_id

        query = self.datastore_client.query(kind=self.datastore_bot_kind)
        query.add_filter("client_id", "=", bot_dict["client_id"])
        query.add_filter("enterprise_id", "=", bot_dict["enterprise_id"])
        query.add_filter("team_id", "=", bot_dict["team_id"])
        query.add_filter("installed_at", "=", bot_dict["installed_at"])

        row_to_update = list(query.fetch(limit=1))

        if row_to_update:
            bot_entity = row_to_update[0]
        else:
            new_key = self._generate_kind_new_key(self.datastore_bot_kind)
            bot_entity: Entity = datastore.Entity(key=new_key, exclude_from_indexes=self.bot_exclude_from_indexes)

        bot_entity.update(**bot_dict)
        self.datastore_client.put(bot_entity)


    def find_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Bot]:
        e_id = enterprise_id or None
        t_id = team_id or None
        if is_enterprise_install:
            t_id = None

        query = self.datastore_client.query(kind=self.datastore_bot_kind)
        query.add_filter("client_id", "=", self.client_id)
        query.add_filter("enterprise_id", "=", e_id)
        query.add_filter("team_id", "=", t_id)

        if self._has_composite_index:
            query.order = ["-installed_at"]

        rows = list(query.fetch(limit=1))

        if rows:
            entity = rows[0]
            return Bot(
                app_id = entity.get("app_id"),
                enterprise_id = entity.get("enterprise_id"),
                enterprise_name = entity.get("enterprise_name"),
                team_id = entity.get("team_id"),
                team_name = entity.get("team_name"),
                bot_token = entity.get("bot_token"),
                bot_id = entity.get("bot_id"),
                bot_user_id = entity.get("bot_user_id"),
                bot_scopes = entity.get("bot_scopes"),
                bot_refresh_token = entity.get("bot_refresh_token"),
                bot_token_expires_at = _to_timestamp(entity.get("bot_token_expires_at")),
                is_enterprise_install = entity.get("is_enterprise_install"),
                installed_at = _to_timestamp(entity.get("installed_at")),
            )

        return None


    def find_installation(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Installation]:
        e_id = enterprise_id or None
        t_id = team_id or None
        if is_enterprise_install:
            t_id = None

        query = self.datastore_client.query(kind=self.datastore_installation_kind)
        query.add_filter("client_id", "=", self.client_id)
        query.add_filter("enterprise_id", "=", e_id)
        query.add_filter("team_id", "=", t_id)

        if user_id is not None:
            query.add_filter("user_id", "=", user_id)

        if self._has_composite_index:
            query.order = ["-installed_at"]

        rows = list(query.fetch(limit=1))

        if rows:
            entity = rows[0]
            return Installation(
                app_id = entity.get("app_id"),
                enterprise_id = entity.get("enterprise_id"),
                enterprise_name = entity.get("enterprise_name"),
                enterprise_url = entity.get("enterprise_url"),
                team_id = entity.get("team_id"),
                team_name = entity.get("team_name"),
                bot_token = entity.get("bot_token"),
                bot_id = entity.get("bot_id"),
                bot_user_id = entity.get("bot_user_id"),
                bot_scopes = entity.get("bot_scopes"),
                bot_refresh_token = entity.get("bot_refresh_token"),
                bot_token_expires_at = _to_timestamp(entity.get("bot_token_expires_at")),
                user_id = entity.get("user_id"),
                user_token = entity.get("user_token"),
                user_scopes = entity.get("user_scopes"),
                user_refresh_token = entity.get("user_refresh_token"),
                user_token_expires_at = _to_timestamp(entity.get("user_token_expires_at")),
                incoming_webhook_url = entity.get("incoming_webhook_url"),
                incoming_webhook_channel = entity.get("incoming_webhook_channel"),
                incoming_webhook_channel_id = entity.get("incoming_webhook_channel_id"),
                incoming_webhook_configuration_url = entity.get("incoming_webhook_configuration_url"),
                is_enterprise_install = entity.get("is_enterprise_install"),
                token_type = entity.get("token_type"),
                installed_at = _to_timestamp(entity.get("installed_at")),
            )

        return None


    def delete_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
    ) -> None:
        query = self.datastore_client.query(kind=self.datastore_bot_kind)
        query.add_filter("client_id", "=", self.client_id)
        query.add_filter("enterprise_id", "=", enterprise_id)
        query.add_filter("team_id", "=", team_id)
        query.keys_only()
        rows = list(query.fetch())
        if rows:
            self.datastore_client.delete_multi(rows)


    def delete_installation(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
    ) -> None:
        query = self.datastore_client.query(kind=self.datastore_installation_kind)
        query.add_filter("client_id", "=", self.client_id)
        query.add_filter("enterprise_id", "=", enterprise_id)
        query.add_filter("team_id", "=", team_id)

        if user_id is not None:
            query.add_filter("user_id", "=", user_id)

        query.keys_only()
        rows = list(query.fetch())
        if rows:
            self.datastore_client.delete_multi(rows)


    def delete_all(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
    ):
        self.delete_bot(enterprise_id=enterprise_id, team_id=team_id)
        self.delete_installation(
            enterprise_id=enterprise_id, team_id=team_id, user_id=None
        )



class GoogleDatastoreOAuthStateStore(OAuthStateStore):
    logger: Logger
    datastore_client: Client
    _datastore_state_kind: str


    def __init__(
        self,
        *,
        datastore_client: Client,
        datastore_state_kind: str,
        expiration_seconds: int,
        logger: Logger,
    ):
        self.datastore_client = datastore_client
        self.expiration_seconds = expiration_seconds
        self._logger = logger
        self._datastore_state_kind = datastore_state_kind


    @property
    def logger(self) -> Logger:
        if self._logger is None:
            self._logger = logging.getLogger(__name__)
        return self._logger


    def consume(self, state: str) -> bool:
        key = self.datastore_client.key(self.datastore_state_kind, state)
        entity = self.datastore_client.get(key)
        if entity is not None:
            self.datastore_client.delete(key)
            now = datetime.now(timezone.utc)
            return entity['expire_at'] > now
        return False


    def issue(self, *args, **kwargs) -> str:
        self.purge_expired_records(10)
        state_value = str(uuid4())
        expire_at = datetime.now(timezone.utc) + timedelta(seconds=self.expiration_seconds)
        key = self.datastore_client.key(self.datastore_state_kind, state_value)
        entity: Entity = datastore.Entity(key=key)
        entity.update({'expire_at': expire_at})
        self.datastore_client.put(entity)
        return state_value


    @property
    def datastore_state_kind(self) -> str:
        return self._datastore_state_kind


    def purge_expired_records(self, max_records_limit=10):
        now = datetime.now(timezone.utc)
        query = self.datastore_client.query(kind=self.datastore_state_kind)
        query.add_filter("expire_at", "<", now)
        query.keys_only()
        expired_records = list(query.fetch(limit=max_records_limit))
        if expired_records:
            self.datastore_client.delete_multi(expired_records)

        return len(expired_records)
