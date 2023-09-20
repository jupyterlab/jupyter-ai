import logging
from typing import Dict, Optional, Tuple, Type, Union
from pandas import json_normalize

from importlib_metadata import entry_points
from jupyter_ai_magics.aliases import MODEL_ID_ALIASES
from jupyter_ai_magics.embedding_providers import BaseEmbeddingsProvider
from jupyter_ai_magics.providers import BaseProvider

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


Logger = Union[logging.Logger, logging.LoggerAdapter]
LmProvidersDict = Dict[str, BaseProvider]
EmProvidersDict = Dict[str, BaseEmbeddingsProvider]
AnyProvider = Union[BaseProvider, BaseEmbeddingsProvider]
ProviderDict = Dict[str, AnyProvider]


def genSankey(df,cat_cols=[],value_cols='',title='Sankey Diagram'):
    # maximum of 6 value cols -> 6 colors
    colorPalette = ['#4B8BBE','#306998','#FFE873','#FFD43B','#646464']
    labelList = []
    colorNumList = []
    for catCol in cat_cols:
        labelListTemp =  list(set(df[catCol].values))
        colorNumList.append(len(labelListTemp))
        labelList = labelList + labelListTemp
        
    # remove duplicates from labelList
    labelList = list(dict.fromkeys(labelList))
    
    # define colors based on number of levels
    colorList = []
    for idx, colorNum in enumerate(colorNumList):
        colorList = colorList + [colorPalette[idx]]*colorNum
        
    # transform df into a source-target pair
    for i in range(len(cat_cols)-1):
        if i==0:
            sourceTargetDf = df[[cat_cols[i],cat_cols[i+1],value_cols]]
            sourceTargetDf.columns = ['source','target','count']
        else:
            tempDf = df[[cat_cols[i],cat_cols[i+1],value_cols]]
            tempDf.columns = ['source','target','count']
            sourceTargetDf = pd.concat([sourceTargetDf,tempDf])
        sourceTargetDf = sourceTargetDf.groupby(['source','target']).agg({'count':'sum'}).reset_index()
        
    # add index for source-target pair
    sourceTargetDf['sourceID'] = sourceTargetDf['source'].apply(lambda x: labelList.index(x))
    sourceTargetDf['targetID'] = sourceTargetDf['target'].apply(lambda x: labelList.index(x))
    
    # creating the sankey diagram
    data = dict(
        type='sankey',
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(
            color = "black",
            width = 0.5
          ),
          label = labelList,
          color = colorList
        ),
        link = dict(
          source = sourceTargetDf['sourceID'],
          target = sourceTargetDf['targetID'],
          value = sourceTargetDf['count']
        )
      )
    
    layout =  dict(
        title = title,
        font = dict(
          size = 10
        )
    )
       
    fig = dict(data=[data], layout=layout)
    return go.Figure(fig)

def load_make_plots(breast_ads_orig):
    def make_plots(patients):
        breast_ads_plot = breast_ads_orig[breast_ads_orig['patientId'].isin( patients)]
        fig = px.histogram(breast_ads_plot, x="diagnosis_date")
        fig.show()
        breast_ads_plot['count']=1
        fig = genSankey(breast_ads_plot, cat_cols=['region','race','icdo3_topography' ],value_cols='count', title="Population Characteristics")
        fig.show()
    return make_plots

def explode_column(df, col_name):
    df2 = df.explode(col_name)
    df3 = json_normalize(df2[col_name].tolist())
    return df2.join(df3)

def explode_columns(df, columns):
    new_df = df
    for col_name in columns:
        new_df = explode_column(new_df, col_name)
    return new_df


def get_lm_providers(log: Optional[Logger] = None) -> LmProvidersDict:
    if not log:
        log = logging.getLogger()
        log.addHandler(logging.NullHandler())

    providers = {}
    eps = entry_points()
    model_provider_eps = eps.select(group="jupyter_ai.model_providers")
    for model_provider_ep in model_provider_eps:
        try:
            provider = model_provider_ep.load()
        except:
            log.error(
                f"Unable to load model provider class from entry point `{model_provider_ep.name}`."
            )
            continue
        providers[provider.id] = provider
        log.info(f"Registered model provider `{provider.id}`.")

    return providers


def get_em_providers(
    log: Optional[Logger] = None,
) -> EmProvidersDict:
    if not log:
        log = logging.getLogger()
        log.addHandler(logging.NullHandler())
    providers = {}
    eps = entry_points()
    model_provider_eps = eps.select(group="jupyter_ai.embeddings_model_providers")
    for model_provider_ep in model_provider_eps:
        try:
            provider = model_provider_ep.load()
        except:
            log.error(
                f"Unable to load embeddings model provider class from entry point `{model_provider_ep.name}`."
            )
            continue
        providers[provider.id] = provider
        log.info(f"Registered embeddings model provider `{provider.id}`.")

    return providers


def decompose_model_id(
    model_id: str, providers: Dict[str, BaseProvider]
) -> Tuple[str, str]:
    """Breaks down a model ID into a two-tuple (provider_id, local_model_id). Returns (None, None) if indeterminate."""
    if model_id in MODEL_ID_ALIASES:
        model_id = MODEL_ID_ALIASES[model_id]

    if ":" not in model_id:
        # case: model ID was not provided with a prefix indicating the provider
        # ID. try to infer the provider ID before returning (None, None).

        # naively search through the dictionary and return the first provider
        # that provides a model of the same ID.
        for provider_id, provider in providers.items():
            if model_id in provider.models:
                return (provider_id, model_id)

        return (None, None)

    provider_id, local_model_id = model_id.split(":", 1)
    return (provider_id, local_model_id)


def get_lm_provider(
    model_id: str, lm_providers: LmProvidersDict
) -> Tuple[str, Type[BaseProvider]]:
    """Gets a two-tuple (<local-model-id>, <provider-class>) specified by a
    global model ID."""
    return _get_provider(model_id, lm_providers)


def get_em_provider(
    model_id: str, em_providers: EmProvidersDict
) -> Tuple[str, Type[BaseEmbeddingsProvider]]:
    """Gets a two-tuple (<local-model-id>, <provider-class>) specified by a
    global model ID."""
    return _get_provider(model_id, em_providers)


def _get_provider(model_id: str, providers: ProviderDict):
    provider_id, local_model_id = decompose_model_id(model_id, providers)
    provider = providers.get(provider_id, None)
    return local_model_id, provider
