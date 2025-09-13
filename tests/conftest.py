import polars as pl
import pytest


@pytest.fixture
def base_df():
    """Para testes de integração/orquestração."""
    return pl.DataFrame(
        {
            "email": ["user@example.com", "alice@ex.com", None],
            "age": [30, 22, 41],
            "city": ["Curitiba", "Joinville", "São Paulo"],
        }
    )


@pytest.fixture
def city_df():
    """Para métodos que atuam em strings/categorias simples."""
    return pl.DataFrame({"city": ["Curitiba", "Joinville", "São Paulo"]})


@pytest.fixture
def numeric_df():
    """Para métodos numéricos (round, noise, bucket, etc.)."""
    return pl.DataFrame({"num": [1.234, 10.0, None, -3.5]})


@pytest.fixture
def df_factory():
    """
    Factory para gerar DataFrames sob demanda:
      df = df_factory(email=["a@b.com", None], age=[1, 2])
    """

    def make(**columns):
        return pl.DataFrame(columns)

    return make


@pytest.fixture
def cfg_factory():
    def make(method: str, column: str, **params):
        node = {"method": method}
        if params:
            node["params"] = params
        return {"columns": {column: node}}

    return make
