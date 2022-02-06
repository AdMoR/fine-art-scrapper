import datetime
import json
from typing import NamedTuple, List

import pandas as pd


class ResultItem(NamedTuple):
    result_id: int
    lot_id: int
    price: float
    currency: str

    def to_json(self):
        return {"result_id": self.result_id, "lot_id": self.lot_id, "price": self.price, "currency": self.currency}


class CatalogItem(NamedTuple):
    catalog_id: int
    lot_id: int
    presentation: str
    result: str
    estimation: str

    def to_json(self):
        return {"catalog_id": self.catalog_id, "lot_id": self.lot_id, "presentation": self.presentation,
                "result": self.result, "estimation": self.estimation}


class DroutSalesElement(NamedTuple):
    catalog_id: int
    title: str
    who: str
    where: str
    when: datetime.datetime
    catalog_elements: List[CatalogItem]
    result_elements: List[ResultItem]

    @property
    def catalog_df(self):
        return pd.DataFrame(self.catalog_elements)

    @property
    def result_df(self):
        return pd.DataFrame(self.result_elements)

    @property
    def is_passed(self):
        return datetime.date.today() - datetime.timedelta(days=7) < self.when

    @property
    def sale_id(self):
        return hash("".join([self.title, self.who]))

    def already_parsed(self, redis_cli):
        return redis_cli.hget("sales",self. catalog_id) is not None

    def redis_serialize(self, redis_cli):
        # Rule : do not serialize active sales, we assume all infos will remain after
        if not self.is_passed:
            return
        if not self.already_parsed(redis_cli):
            redis_cli.hset("sales", self.sale_id,
                           json.dumps({"id": self.catalog_id, "title": self.title, "who": self.who,
                                       "where": self.where, "when": str(self.when)})
                           )
            for cata in self.catalog_elements:
                redis_cli.hset("catalog_item", cata.lot_id, cata.to_json())
            for rez in self.result_elements:
                redis_cli.hset("result_item", rez.result_id, rez.to_json())
